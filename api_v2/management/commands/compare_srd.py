"""Management command to compare SRD PDF content against the database."""
from __future__ import annotations
import os
import time
import concurrent.futures
from dataclasses import dataclass
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from data.raw_sources.srd_5_2.parsers.base import slugify, clean_text


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------


@dataclass
class FieldMismatch:
    entity_name: str
    field: str
    pdf_value: Any
    db_value: Any


@dataclass
class ComparisonResult:
    entity_type: str
    pdf_count: int
    db_count: int
    missing: list[str]
    extra: list[str]
    mismatches: list[FieldMismatch]


# ---------------------------------------------------------------------------
# Field maps: pdf record attribute → DB values() key
# ---------------------------------------------------------------------------

_FIELD_MAPS: dict[str, dict[str, str]] = {
    "spells": {
        "level": "level",
        "school": "school__name",
        "casting_time": "casting_time",
        "range_text": "range_text",
        "verbal": "verbal",
        "somatic": "somatic",
        "material": "material",
        "duration": "duration",
        "concentration": "concentration",
        "ritual": "ritual",
    },
    "creatures": {
        "armor_class": "armor_class",
        "hit_points": "hit_points",
        "strength": "ability_score_strength",
        "dexterity": "ability_score_dexterity",
        "constitution": "ability_score_constitution",
        "intelligence": "ability_score_intelligence",
        "wisdom": "ability_score_wisdom",
        "charisma": "ability_score_charisma",
        "challenge_rating": "challenge_rating",
        "walk": "walk",
        "fly": "fly",
        "swim": "swim",
        "burrow": "burrow",
        "climb": "climb",
    },
    "weapons": {
        "damage_type": "damage_type__name",
    },
    "armor": {
        "ac_base": "ac_base",
        "ac_add_dex": "ac_add_dexmod",
        "strength_required": "strength_score_required",
        "stealth_disadvantage": "grants_stealth_disadvantage",
    },
    "magic_items": {
        "rarity": "rarity__name",
        "requires_attunement": "requires_attunement",
    },
}

SKIP_FIELDS: dict[str, set[str]] = {
    "spells": {"desc", "higher_level", "material_specified"},
    "creatures": {"desc", "traits", "actions", "size", "type", "alignment",
                  "hit_dice", "hover", "damage_immunities", "damage_resistances",
                  "damage_vulnerabilities", "condition_immunities",
                  "darkvision_range", "blindsight_range", "truesight_range"},
    "weapons": {"desc", "mastery_desc", "cost", "damage"},
    "armor": {"desc", "cost", "ac_cap_dex"},
    "magic_items": {"desc"},
}


# ---------------------------------------------------------------------------
# Pure diff logic
# ---------------------------------------------------------------------------


def _normalize(value: Any) -> Any:
    if isinstance(value, str):
        return clean_text(value).lower().strip()
    if isinstance(value, (list, tuple)):
        return sorted(_normalize(v) for v in value)
    return value


def _values_equal(a: Any, b: Any) -> bool:
    if isinstance(a, float) or isinstance(b, float):
        try:
            return abs(float(a) - float(b)) < 0.001
        except (TypeError, ValueError):
            return False
    return _normalize(a) == _normalize(b)


def compare_records(
    entity_type: str,
    pdf_records: list,
    db_records: list[dict],
    skip_fields: set[str],
) -> ComparisonResult:
    """Pure function: compare PDF records against DB records, returning diffs."""
    pdf_by_slug = {slugify(r.name): r for r in pdf_records}
    db_by_slug = {slugify(r["name"]): r for r in db_records}

    missing = sorted(pdf_by_slug[s].name for s in pdf_by_slug if s not in db_by_slug)
    extra = sorted(db_by_slug[s]["name"] for s in db_by_slug if s not in pdf_by_slug)

    field_map = _FIELD_MAPS.get(entity_type, {})
    mismatches: list[FieldMismatch] = []
    for slug in pdf_by_slug:
        if slug not in db_by_slug:
            continue
        pdf_rec = pdf_by_slug[slug]
        db_rec = db_by_slug[slug]
        for field, db_key in field_map.items():
            if field in skip_fields:
                continue
            pdf_val = getattr(pdf_rec, field, None)
            db_val = db_rec.get(db_key)
            if not _values_equal(pdf_val, db_val):
                mismatches.append(FieldMismatch(
                    entity_name=pdf_rec.name,
                    field=field,
                    pdf_value=pdf_val,
                    db_value=db_val,
                ))

    return ComparisonResult(
        entity_type=entity_type,
        pdf_count=len(pdf_by_slug),
        db_count=len(db_by_slug),
        missing=missing,
        extra=extra,
        mismatches=mismatches,
    )


# ---------------------------------------------------------------------------
# Runner functions — each opens the PDF independently (thread-safe)
# ---------------------------------------------------------------------------


def _run_spell_comparison(pdf_path: str, document: str) -> ComparisonResult:
    from api_v2.models import Spell
    from data.raw_sources.srd_5_2.parsers.spells import extract_spells_from_pdf
    pdf_records = extract_spells_from_pdf(pdf_path)
    db_records = list(Spell.objects.filter(document_id=document).values(
        "name", "level", "school__name", "casting_time", "range_text",
        "verbal", "somatic", "material", "duration", "concentration", "ritual",
    ))
    return compare_records("spells", pdf_records, db_records, SKIP_FIELDS["spells"])


def _run_creature_comparison(pdf_path: str, document: str) -> ComparisonResult:
    from api_v2.models import Creature
    from data.raw_sources.srd_5_2.parsers.creatures import extract_creatures_from_pdf
    pdf_records = extract_creatures_from_pdf(pdf_path)
    db_records = list(Creature.objects.filter(document_id=document).values(
        "name", "armor_class", "hit_points", "challenge_rating",
        "ability_score_strength", "ability_score_dexterity", "ability_score_constitution",
        "ability_score_intelligence", "ability_score_wisdom", "ability_score_charisma",
        "walk", "fly", "swim", "burrow", "climb",
    ))
    return compare_records("creatures", pdf_records, db_records, SKIP_FIELDS["creatures"])


def _run_weapon_comparison(pdf_path: str, document: str) -> ComparisonResult:
    from api_v2.models import Weapon
    from data.raw_sources.srd_5_2.parsers.items import extract_weapons_from_pdf
    pdf_records = extract_weapons_from_pdf(pdf_path)
    db_records = list(Weapon.objects.filter(document_id=document).values(
        "name", "damage_type__name",
    ))
    return compare_records("weapons", pdf_records, db_records, SKIP_FIELDS["weapons"])


def _run_armor_comparison(pdf_path: str, document: str) -> ComparisonResult:
    from api_v2.models import Armor
    from data.raw_sources.srd_5_2.parsers.items import extract_armor_from_pdf
    pdf_records = extract_armor_from_pdf(pdf_path)
    db_records = list(Armor.objects.filter(document_id=document).values(
        "name", "ac_base", "ac_add_dexmod", "strength_score_required",
        "grants_stealth_disadvantage",
    ))
    return compare_records("armor", pdf_records, db_records, SKIP_FIELDS["armor"])


def _run_magic_item_comparison(pdf_path: str, document: str) -> ComparisonResult:
    from api_v2.models import MagicItem
    from data.raw_sources.srd_5_2.parsers.items import extract_magic_items_from_pdf
    pdf_records = extract_magic_items_from_pdf(pdf_path)
    db_records = list(MagicItem.objects.filter(document_id=document).values(
        "name", "rarity__name", "requires_attunement",
    ))
    return compare_records("magic_items", pdf_records, db_records, SKIP_FIELDS["magic_items"])


_RUNNERS = {
    "spells": _run_spell_comparison,
    "creatures": _run_creature_comparison,
    "weapons": _run_weapon_comparison,
    "armor": _run_armor_comparison,
    "magic_items": _run_magic_item_comparison,
}


# ---------------------------------------------------------------------------
# Rich rendering
# ---------------------------------------------------------------------------


def _render_results(results: dict[str, ComparisonResult], elapsed: float) -> None:
    console = Console()

    summary = Table(title=f"SRD 5.2 PDF vs Database  (completed in {elapsed:.1f}s)")
    summary.add_column("Entity type", style="bold")
    summary.add_column("In PDF", justify="right")
    summary.add_column("In DB", justify="right")
    summary.add_column("Missing", justify="right")
    summary.add_column("Extra", justify="right")
    summary.add_column("Mismatches", justify="right")

    for name, result in results.items():
        def _fmt(n):
            return f"[green]0[/green]" if n == 0 else str(n)
        summary.add_row(
            name,
            str(result.pdf_count),
            str(result.db_count),
            _fmt(len(result.missing)),
            _fmt(len(result.extra)),
            _fmt(len(result.mismatches)),
        )
    console.print(summary)

    for name, result in results.items():
        if result.missing:
            console.print(Panel(
                "\n".join(f"• {n}" for n in result.missing),
                title=f"Missing from DB — {name}",
                border_style="red",
            ))
        if result.extra:
            console.print(Panel(
                "\n".join(f"• {n}" for n in result.extra),
                title=f"Extra in DB — {name}",
                border_style="yellow",
            ))
        if result.mismatches:
            t = Table(title=f"Field mismatches — {name}")
            t.add_column("Entity")
            t.add_column("Field")
            t.add_column("PDF value", style="green")
            t.add_column("DB value", style="red")
            for mm in result.mismatches:
                t.add_row(mm.entity_name, mm.field, str(mm.pdf_value), str(mm.db_value))
            console.print(t)


# ---------------------------------------------------------------------------
# Command
# ---------------------------------------------------------------------------

DEFAULT_PDF = os.path.normpath(os.path.join(
    os.path.dirname(__file__),
    "../../../../data/raw_sources/srd_5_2/SRD_CC_v5.2.pdf",
))


class Command(BaseCommand):
    help = "Compare SRD PDF content against the database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--pdf",
            default=DEFAULT_PDF,
            help="Path to SRD PDF file.",
        )
        parser.add_argument(
            "--document",
            default="srd-2024",
            help="Document slug to compare against.",
        )
        parser.add_argument(
            "--entity",
            choices=[*_RUNNERS.keys(), "all"],
            default="all",
            help="Entity type to compare (default: all).",
        )

    def handle(self, *args, **options):
        pdf_path = options["pdf"]
        document = options["document"]
        entity = options["entity"]

        if not os.path.exists(pdf_path):
            raise CommandError(f"PDF not found: {pdf_path}")

        entity_types = list(_RUNNERS.keys()) if entity == "all" else [entity]

        start = time.monotonic()
        results: dict[str, ComparisonResult] = {}

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(_RUNNERS[etype], pdf_path, document): etype
                for etype in entity_types
            }
            for future in concurrent.futures.as_completed(futures):
                etype = futures[future]
                try:
                    results[etype] = future.result()
                except Exception as exc:
                    self.stderr.write(f"  ERROR comparing {etype}: {exc}")

        elapsed = time.monotonic() - start
        _render_results(
            {k: results[k] for k in entity_types if k in results},
            elapsed,
        )
