"""Management command to compare SRD PDF content against the database."""
from __future__ import annotations
import os
import re
import time
import traceback
import concurrent.futures
from dataclasses import dataclass, field
from difflib import SequenceMatcher
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
    page_number: int = 0   # PDF page where the entity appears (0 = unknown)
    subtype: str = ""      # for desc fields: "text" or "format"


@dataclass
class ComparisonResult:
    entity_type: str
    pdf_count: int
    db_count: int
    missing: list[str]
    extra: list[str]
    mismatches: list[FieldMismatch]
    missing_pages: dict[str, int] = field(default_factory=dict)  # name → PDF page


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
        "desc": "desc",
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
        "desc": "desc",
    },
    "classes": {
        "hit_dice": "hit_dice",
    },
    "feats": {
        "feat_type": "type",
        "prerequisite": "prerequisite",
    },
    "species": {
        "speed_text": "speed_text",
    },
}

SKIP_FIELDS: dict[str, set[str]] = {
    "spells": {"higher_level", "material_specified"},
    "creatures": {"desc", "traits", "actions", "size", "type", "alignment",
                  "hit_dice", "hover", "damage_immunities", "damage_resistances",
                  "damage_vulnerabilities", "condition_immunities",
                  "darkvision_range", "blindsight_range", "truesight_range"},
    "weapons": {"desc", "mastery_desc", "cost", "damage"},
    "armor": {"desc", "cost", "ac_cap_dex"},
    "magic_items": set(),
    "classes": {"desc"},
    "feats": {"desc"},
    "species": {"desc"},
}


# ---------------------------------------------------------------------------
# Pure diff logic
# ---------------------------------------------------------------------------


# Issue 1 (duration): strips "Concentration, up to " / "Up to " prefixes so PDF
# durations like "Concentration, up to 1 minute" match DB value "1 minute".
_DURATION_PREFIX_RE = re.compile(
    r"^(?:concentration,?\s+)?up\s+to\s+", re.IGNORECASE
)
# Issue 1 (duration): normalises plural time units to singular to match DB convention
# ("8 hours" → "8 hour", "10 minutes" → "10 minute", etc.).
_TIME_PLURAL_RE = re.compile(
    r"\b(hour|minute|day|round|week|month|year)s\b", re.IGNORECASE
)
# Issue A (casting_time): DB stores bare unit without count ("minute" not "1 minute").
# Applied only inside _values_equal when field=="casting_time".
_CAST_TIME_COUNT_RE = re.compile(r"^\d+\s+")


def _normalize(value: Any) -> Any:
    if isinstance(value, str):
        s = clean_text(value).lower().strip()
        # Issue 1 — duration prefix / plural
        s = _DURATION_PREFIX_RE.sub("", s)
        s = _TIME_PLURAL_RE.sub(r"\1", s)
        # Issue D — "Reaction, which you take…" and "Bonus Action, which you take immedi-"
        # (PDF line-wrap artifact): strip ", which …" suffix before further transforms.
        s = re.sub(r",\s+which\b.*$", "", s)
        # Issue B — "Bonus Action" → DB slug "bonus-action"
        s = re.sub(r"\bbonus action\b", "bonus-action", s)
        # Issue C — DB stores ritual as a separate boolean; strip " or Ritual" suffix
        s = re.sub(r"\s+or\s+ritual\b.*$", "", s)
        return s
    if isinstance(value, (list, tuple)):
        return sorted(_normalize(v) for v in value)
    return value


_DESC_TEXT_THRESHOLD = 0.80   # word-level ratio below this → text content substantially differs
_DESC_EMPTY_THRESHOLD = 10    # words below which a description is treated as absent


def _strip_markdown(text: str) -> str:
    """Strip markdown syntax to produce the plain text a reader would see.

    Applied to the DB side before comparison so that markdown formatting
    differences don't inflate the apparent text distance.
    """
    if not text:
        return ""
    # ATX headers: ## Heading → Heading
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # Bold / italic: **x**, *x*, __x__, _x_
    text = re.sub(r"\*{1,2}([^*\n]+)\*{1,2}", r"\1", text)
    text = re.sub(r"_{1,2}([^_\n]+)_{1,2}", r"\1", text)
    # Inline code: `code`
    text = re.sub(r"`([^`\n]+)`", r"\1", text)
    # Links / images: [label](url) → label
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)
    # Table separator rows: |---|---| (discard)
    text = re.sub(r"^\|[-:| ]+\|$", "", text, flags=re.MULTILINE)
    # Table data rows: | cell | cell | → cells joined with space
    text = re.sub(r"\|([^|\n]+)", lambda m: m.group(1) + " ", text)
    text = re.sub(r"\|$", "", text, flags=re.MULTILINE)
    # Unordered / ordered list markers
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+[.)]\s+", "", text, flags=re.MULTILINE)
    # Blockquotes and horizontal rules
    text = re.sub(r"^>\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)
    return text


_SRD_FOOTER_RE = re.compile(
    r"\d+\s*system\s+reference\s+document\s+[\d.]+", re.IGNORECASE
)


def _normalize_desc(text: str) -> str:
    """Normalize plain description text for similarity comparison.

    - Strips SRD page-footer lines that the PDF extractor sometimes absorbs
      into description blocks (e.g. '107system reference document 5.2').
    - Re-joins PDF line-break hyphens ('concentra-\\ntion' → 'concentration').
    - Applies standard clean_text and lowercasing.

    Call _strip_markdown on the DB side before this.
    """
    if not text:
        return ""
    text = _SRD_FOOTER_RE.sub(" ", text)
    text = re.sub(r"(\w)-\s+(\w)", r"\1\2", text)
    return clean_text(text).lower().strip()


def _to_word_tokens(normalized_text: str) -> list[str]:
    """Split normalized text into a word token list, stripping punctuation.

    Comparing token lists rather than character strings makes the similarity
    metric forgiving of punctuation variants (curly quotes, en/em dashes,
    bullet characters, comma placement) while remaining sensitive to actual
    content differences (wrong words, missing sentences, wrong numbers).
    """
    return re.sub(r"[^a-z0-9]", " ", normalized_text).split()


def _pdf_has_list_content(pdf_text: str) -> bool:
    """Heuristic: does the raw PDF text suggest enumerated list content?

    Looks for explicit bullet characters that pdfplumber extracts from the
    PDF, or for numbered list patterns like '1.' / '1)' starting a line.
    """
    if re.search(r"[•·◦▪▸►]", pdf_text):
        return True
    return bool(re.search(r"^\s*\d+[.)]\s+\S", pdf_text, re.MULTILINE))


def _db_has_markdown_lists(db_markdown: str) -> bool:
    """True when the DB description contains explicit markdown list syntax."""
    return bool(re.search(r"^\s*[-*+]\s+|^\s*\d+[.)]\s+", db_markdown, re.MULTILINE))


def _compare_desc(pdf_text: str, db_markdown: str) -> tuple[str, float]:
    """Compare a PDF plain-text description against a DB markdown description.

    Returns ``(mismatch_type, word_similarity_ratio)`` where mismatch_type is:
    - ``"match"``   — equivalent at the content level
    - ``"text"``    — content substantially differs (wrong/missing words)
    - ``"format"``  — content is similar but PDF has list/table structure
                      that the DB markdown does not encode

    Uses word-token-level SequenceMatcher rather than character-level so that
    punctuation variants (bullets, quotes, dashes) and PDF extraction
    artefacts (page footers, minor whitespace) don't inflate the distance.
    """
    db_plain = _strip_markdown(db_markdown or "")
    pdf_norm = _normalize_desc(pdf_text or "")
    db_norm = _normalize_desc(db_plain)

    pdf_tokens = _to_word_tokens(pdf_norm)
    db_tokens = _to_word_tokens(db_norm)

    if not pdf_tokens and not db_tokens:
        return "match", 1.0
    if not pdf_tokens or not db_tokens:
        if max(len(pdf_tokens), len(db_tokens)) < _DESC_EMPTY_THRESHOLD:
            return "match", 1.0
        return "text", 0.0

    ratio = SequenceMatcher(None, pdf_tokens, db_tokens).ratio()

    if ratio < _DESC_TEXT_THRESHOLD:
        return "text", ratio

    # Content is similar — check for missing markdown structure.
    if _pdf_has_list_content(pdf_text or "") and not _db_has_markdown_lists(db_markdown or ""):
        return "format", ratio

    return "match", ratio


def _desc_diff_context(pdf_text: str, db_markdown: str, window: int = 8) -> str:
    """Return a short snippet showing WHERE the two descriptions first diverge.

    Compares at the word-token level so punctuation differences are invisible.
    Returns an empty string when there is no divergence.
    """
    db_plain = _strip_markdown(db_markdown or "")
    pdf_tokens = _to_word_tokens(_normalize_desc(pdf_text or ""))
    db_tokens = _to_word_tokens(_normalize_desc(db_plain))

    # Find the index of the first word that differs
    first_diff = next(
        (i for i, (p, d) in enumerate(zip(pdf_tokens, db_tokens)) if p != d),
        None,
    )

    if first_diff is None:
        # Texts agree up to the shorter one — the longer has extra content
        shorter, longer, label = (
            (pdf_tokens, db_tokens, "DB extra")
            if len(pdf_tokens) < len(db_tokens)
            else (db_tokens, pdf_tokens, "PDF extra")
        )
        if len(longer) <= len(shorter):
            return ""
        extra = " ".join(longer[len(shorter): len(shorter) + window])
        return f"{label} at word {len(shorter) + 1}: '{extra}…'"

    start = max(0, first_diff - 2)
    pdf_ctx = " ".join(pdf_tokens[start: first_diff + window])
    db_ctx = " ".join(db_tokens[start: first_diff + window])
    return f"diverges at word {first_diff + 1} — PDF: '{pdf_ctx}…' | DB: '{db_ctx}…'"


def _values_equal(a: Any, b: Any, field: str = "") -> bool:
    if isinstance(a, float) or isinstance(b, float):
        try:
            return abs(float(a) - float(b)) < 0.001
        except (TypeError, ValueError):
            return False
    na, nb = _normalize(a), _normalize(b)
    # Issue A — casting_time: DB strips leading count ("1 minute" → "minute")
    if field == "casting_time":
        if isinstance(na, str):
            na = _CAST_TIME_COUNT_RE.sub("", na)
        if isinstance(nb, str):
            nb = _CAST_TIME_COUNT_RE.sub("", nb)
    return na == nb


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
    missing_pages = {
        pdf_by_slug[s].name: getattr(pdf_by_slug[s], "page_number", 0)
        for s in pdf_by_slug if s not in db_by_slug
    }

    field_map = _FIELD_MAPS.get(entity_type, {})
    mismatches: list[FieldMismatch] = []
    for slug in pdf_by_slug:
        if slug not in db_by_slug:
            continue
        pdf_rec = pdf_by_slug[slug]
        db_rec = db_by_slug[slug]
        page_num = getattr(pdf_rec, "page_number", 0)
        for pdf_field, db_key in field_map.items():
            if pdf_field in skip_fields:
                continue
            pdf_val = getattr(pdf_rec, pdf_field, None)
            db_val = db_rec.get(db_key)
            if pdf_field == "desc":
                mismatch_type, _ratio = _compare_desc(pdf_val or "", db_val or "")
                if mismatch_type != "match":
                    mismatches.append(FieldMismatch(
                        entity_name=pdf_rec.name,
                        field=pdf_field,
                        pdf_value=pdf_val,
                        db_value=db_val,
                        page_number=page_num,
                        subtype=mismatch_type,
                    ))
            else:
                if not _values_equal(pdf_val, db_val, field=pdf_field):
                    mismatches.append(FieldMismatch(
                        entity_name=pdf_rec.name,
                        field=pdf_field,
                        pdf_value=pdf_val,
                        db_value=db_val,
                        page_number=page_num,
                    ))

    return ComparisonResult(
        entity_type=entity_type,
        pdf_count=len(pdf_by_slug),
        db_count=len(db_by_slug),
        missing=missing,
        extra=extra,
        mismatches=mismatches,
        missing_pages=missing_pages,
    )


# ---------------------------------------------------------------------------
# Enchantment-aware magic item comparison
# ---------------------------------------------------------------------------

# The 52 item types that appear in "[ItemType] (+X)" DB entries correspond to three
# PDF enchantment categories (Weapon, Armor, Shield), with Ammunition mapping directly.
# Rarity is determined by bonus level: +1=Uncommon, +2=Rare, +3=Very Rare.
_BONUS_WEAPON_TYPES: frozenset[str] = frozenset({
    "battleaxe", "blowgun", "club", "dagger", "dart", "flail", "glaive", "greataxe",
    "greatclub", "greatsword", "halberd", "hand crossbow", "handaxe", "heavy crossbow",
    "javelin", "lance", "light crossbow", "light hammer", "longbow", "longsword", "mace",
    "maul", "morningstar", "musket", "pike", "pistol", "quarterstaff", "rapier",
    "scimitar", "shortbow", "shortsword", "sickle", "sling", "spear", "trident",
    "war pick", "warhammer", "whip",
})
_BONUS_ARMOR_TYPES: frozenset[str] = frozenset({
    "breastplate", "chain mail", "chain shirt", "half plate armor", "hide armor",
    "leather armor", "padded armor", "plate armor", "ring mail", "scale mail",
    "splint armor", "studded leather armor",
})

# Single-word weapon or armor type suffixes that the DB appends to enchantment names.
# e.g. "Flame Tongue Longsword" → strip "Longsword" → enchantment "Flame Tongue"
# e.g. "Elven Chain Mail" → strip "Mail" → enchantment "Elven Chain"
_ITEM_TYPE_SUFFIXES: frozenset[str] = frozenset({
    # Weapons
    "battleaxe", "club", "dagger", "dart", "flail", "glaive", "greataxe", "greatclub",
    "greatsword", "halberd", "handaxe", "javelin", "lance", "longsword", "mace", "maul",
    "morningstar", "pike", "quarterstaff", "rapier", "scimitar", "shortbow", "shortsword",
    "sickle", "sling", "spear", "trident", "warhammer", "whip", "longbow", "blowgun",
    "musket", "pistol",
    # Armor words that appear as last word in compound names
    "breastplate", "mail", "shirt", "armor", "leather", "padded", "splint",
})

# Sword-like weapon types that the DB uses when expanding PDF's generic "Sword of X".
# e.g. "Longsword of Sharpness" / "Glaive of Life Stealing" → normalise to "sword-of-X"
_SWORD_EXPANDABLES: frozenset[str] = frozenset({
    "glaive", "greatsword", "longsword", "rapier", "scimitar", "shortsword",
})

# Slugs of "of X" suffixes that identify the SRD's multi-weapon-type enchantments.
# Only these trigger Pass 4 normalisation — actual named items like "Scimitar of Speed"
# are excluded because "of-speed" is not in this set.
_SWORD_OF_ENCHANTMENT_SLUGS: frozenset[str] = frozenset({
    "of-life-stealing", "of-sharpness", "of-wounding",
})

# Generic item-category words that sometimes appear at the end of PDF enchantment names
# e.g. "Berserker Axe" → base enchantment "Berserker"; DB has "Berserker Battleaxe"
_GENERIC_CATEGORY_SUFFIXES: frozenset[str] = frozenset({
    "axe", "sword", "armor", "chain", "weapon", "shield",
})


def _db_enchantment_slug(db_name: str) -> str:
    """Derive the enchantment slug from a DB magic item name.

    Passes applied in priority order:

    1. "[ItemType] (+X)": maps to generic PDF category
       ("weapon", "armor", "shield", "ammunition").
    1b. "[Name] +N" trailing bonus (no parens): strip the bonus suffix.
       e.g. "Wand of the War Mage +1" → "wand-of-the-war-mage".
    1c. "Ammunition of [CreatureType] Slaying": normalise to "ammunition-of-slaying".
    2. Strip parenthetical: "Adamantine Armor (Breastplate)" → "Adamantine Armor".
    3. Strip trailing item-type suffix (two-word checked before single-word, only
       without a parenthetical): "Flame Tongue War Pick" → "Flame Tongue".
    4. Normalise "[sword-expandable weapon] of X" → "Sword of X" so that the DB's
       many specific weapon type expansions match the PDF's generic "Sword of X" entry.
    """
    # Pass 1: bonus-enhancement "[ItemType] (+X)" → generic category
    m = re.match(r"^(.+)\s*\(\+\d\)$", db_name)
    if m:
        item_type = m.group(1).strip().lower()
        if item_type == "ammunition":
            return "ammunition"
        if item_type == "shield":
            return "shield"
        if item_type in _BONUS_WEAPON_TYPES:
            return "weapon"
        if item_type in _BONUS_ARMOR_TYPES:
            return "armor"

    # Pass 1b: "[Name] +N" trailing space-plus-digit (not parenthesised) → strip
    stripped = re.sub(r"\s+\+\d+\s*$", "", db_name).strip()
    if stripped != db_name:
        return _db_enchantment_slug(stripped)

    # Pass 1c: "Ammunition of [CreatureType] Slaying" → "ammunition-of-slaying"
    if re.match(r"^Ammunition\s+of\s+\S+\s+Slaying$", db_name, re.IGNORECASE):
        return "ammunition-of-slaying"

    # Pass 2: strip parenthetical
    had_paren = bool(re.search(r"\s*\([^)]*\)\s*$", db_name))
    base = re.sub(r"\s*\([^)]*\)\s*$", "", db_name).strip()

    # Pass 3: strip trailing item-type suffix (only when no parenthetical was present).
    # Two-word weapon types (e.g. "War Pick", "Light Hammer") are checked first.
    if not had_paren:
        words = base.split()
        if len(words) >= 3:
            two_word = (words[-2] + " " + words[-1]).lower()
            if two_word in _BONUS_WEAPON_TYPES:
                base = " ".join(words[:-2]).strip()
            elif words[-1].lower() in _ITEM_TYPE_SUFFIXES:
                base = " ".join(words[:-1]).strip()
        elif len(words) == 2 and words[-1].lower() in _ITEM_TYPE_SUFFIXES:
            base = words[0].strip()

    # Pass 4: normalise "[sword-expandable weapon] of X" → "Sword of X", but only for
    # the known multi-weapon-type enchantments (Life Stealing, Sharpness, Wounding).
    # Named items like "Scimitar of Speed" are excluded by the slug whitelist.
    parts = base.split(None, 1)
    if (len(parts) == 2
            and parts[0].lower() in _SWORD_EXPANDABLES
            and parts[1].lower().startswith("of ")):
        if slugify(parts[1]) in _SWORD_OF_ENCHANTMENT_SLUGS:
            base = "Sword " + parts[1]

    return slugify(base)


def _enchantment_slugs_match(pdf_slug: str, db_slug: str) -> bool:
    """True when the two slugs refer to the same enchantment concept.

    Exact match covers most cases.  A soft match handles PDF names that include a
    trailing generic item-category word absent from the DB slug, e.g.:
      PDF "berserker-axe"  ↔  DB "berserker"   (generic "axe" stripped from PDF)
      PDF "dancing-sword"  ↔  DB "dancing"      (generic "sword" stripped from PDF)
    """
    if pdf_slug == db_slug:
        return True
    if pdf_slug.startswith(db_slug + "-"):
        suffix = pdf_slug[len(db_slug) + 1:]
        if suffix in _GENERIC_CATEGORY_SUFFIXES:
            return True
    return False


def compare_magic_item_enchantments(
    pdf_records: list,
    db_records: list[dict],
    skip_fields: set[str],
) -> ComparisonResult:
    """Compare PDF magic item enchantments against DB records.

    Rather than matching on exact name, this function operates at the
    *enchantment* level:
    - PDF records use enchantment_name (bonus-variant suffix stripped from name).
    - DB records are grouped by their derived enchantment name (parenthetical and
      trailing item-type word stripped).

    This means "Weapon, +1, +2, or +3" (PDF enchantment "Weapon") correctly
    aligns with the DB's many specific "+1" weapon entries, and "Adamantine Armor"
    aligns with "Adamantine Armor (Breastplate)", "(Chain Mail)", etc.
    """
    # PDF: keyed by enchantment slug.  Strip any parenthetical from the enchantment name
    # (e.g. "Stone of Good Luck (Luckstone)" → "Stone of Good Luck") before slugifying
    # so that DB entries without the parenthetical still match.
    pdf_by_esl: dict[str, Any] = {}
    for r in pdf_records:
        clean = re.sub(r"\s*\([^)]*\)", "", r.enchantment_name).strip()
        esl = slugify(clean)
        pdf_by_esl.setdefault(esl, r)  # first seen wins for duplicates

    # DB: group by enchantment slug
    db_groups: dict[str, list[dict]] = {}
    for r in db_records:
        esl = _db_enchantment_slug(r["name"])
        db_groups.setdefault(esl, []).append(r)

    # Build a sorted list of all DB enchantment slugs for look-up
    db_esls: list[str] = sorted(db_groups)

    def _pdf_in_db(pdf_slug: str) -> bool:
        return any(_enchantment_slugs_match(pdf_slug, ds) for ds in db_esls)

    def _db_in_pdf(db_slug: str) -> bool:
        return any(_enchantment_slugs_match(ps, db_slug) for ps in pdf_by_esl)

    missing = sorted(
        pdf_by_esl[s].enchantment_name
        for s in pdf_by_esl
        if not _pdf_in_db(s)
    )
    missing_pages = {
        pdf_by_esl[s].enchantment_name: getattr(pdf_by_esl[s], "page_number", 0)
        for s in pdf_by_esl if not _pdf_in_db(s)
    }
    extra_names: list[str] = []
    for db_slug, group in db_groups.items():
        if not _db_in_pdf(db_slug):
            # Report a human-readable enchantment name for the extra group.
            # Mirror _db_enchantment_slug's normalization but preserve casing.
            raw = group[0]["name"]
            had_paren = bool(re.search(r"\s*\([^)]*\)\s*$", raw))
            ench_name = re.sub(r"\s*\([^)]*\)\s*$", "", raw).strip()
            if not had_paren:
                words = ench_name.split()
                if len(words) >= 3:
                    two_word = (words[-2] + " " + words[-1]).lower()
                    if two_word in _BONUS_WEAPON_TYPES:
                        ench_name = " ".join(words[:-2]).strip()
                    elif words[-1].lower() in _ITEM_TYPE_SUFFIXES:
                        ench_name = " ".join(words[:-1]).strip()
                elif len(words) == 2 and words[-1].lower() in _ITEM_TYPE_SUFFIXES:
                    ench_name = words[0].strip()
            extra_names.append(ench_name)
    extra = sorted(set(extra_names))

    # Field comparison: for each PDF enchantment, compare against a representative
    # DB record from its matching group.
    field_map = _FIELD_MAPS.get("magic_items", {})
    mismatches: list[FieldMismatch] = []
    for pdf_slug, pdf_rec in pdf_by_esl.items():
        # Find matching DB group
        matched_group: list[dict] | None = None
        for db_slug, group in db_groups.items():
            if _enchantment_slugs_match(pdf_slug, db_slug):
                matched_group = group
                break
        if matched_group is None:
            continue
        db_rep = matched_group[0]  # representative record
        page_num = getattr(pdf_rec, "page_number", 0)
        for pdf_field, db_key in field_map.items():
            if pdf_field in skip_fields:
                continue
            pdf_val = getattr(pdf_rec, pdf_field, None)
            db_val = db_rep.get(db_key)
            if pdf_field == "desc":
                mismatch_type, _ratio = _compare_desc(pdf_val or "", db_val or "")
                if mismatch_type == "match":
                    continue
                mismatches.append(FieldMismatch(
                    entity_name=pdf_rec.enchantment_name,
                    field=pdf_field,
                    pdf_value=pdf_val,
                    db_value=db_val,
                    page_number=page_num,
                    subtype=mismatch_type,
                ))
            elif not _values_equal(pdf_val, db_val, field=pdf_field):
                mismatches.append(FieldMismatch(
                    entity_name=pdf_rec.enchantment_name,
                    field=pdf_field,
                    pdf_value=pdf_val,
                    db_value=db_val,
                    page_number=page_num,
                ))

    return ComparisonResult(
        entity_type="magic_items",
        pdf_count=len(pdf_by_esl),
        db_count=len(db_records),
        missing=missing,
        extra=extra,
        mismatches=mismatches,
        missing_pages=missing_pages,
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
        "verbal", "somatic", "material", "duration", "concentration", "ritual", "desc",
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
        "name", "rarity__name", "requires_attunement", "desc",
    ))
    return compare_magic_item_enchantments(pdf_records, db_records, SKIP_FIELDS["magic_items"])


def _run_class_comparison(pdf_path: str, document: str) -> ComparisonResult:
    from api_v2.models import CharacterClass
    from data.raw_sources.srd_5_2.parsers.classes import extract_classes_from_pdf
    pdf_records = extract_classes_from_pdf(pdf_path)
    db_records = list(
        CharacterClass.objects.filter(document_id=document, subclass_of=None)
        .values("name", "hit_dice")
    )
    return compare_records("classes", pdf_records, db_records, SKIP_FIELDS["classes"])


def _run_feat_comparison(pdf_path: str, document: str) -> ComparisonResult:
    from api_v2.models import Feat
    from data.raw_sources.srd_5_2.parsers.origins import extract_feats_from_pdf
    pdf_records = extract_feats_from_pdf(pdf_path)
    db_records = list(
        Feat.objects.filter(document_id=document)
        .values("name", "type", "prerequisite")
    )
    return compare_records("feats", pdf_records, db_records, SKIP_FIELDS["feats"])


def _run_species_comparison(pdf_path: str, document: str) -> ComparisonResult:
    from api_v2.models import Species, SpeciesTrait
    from data.raw_sources.srd_5_2.parsers.origins import extract_species_from_pdf
    pdf_records = extract_species_from_pdf(pdf_path)
    speed_by_name = {
        t["parent__name"]: t["desc"]
        for t in SpeciesTrait.objects.filter(
            type="SPEED",
            parent__document_id=document,
            parent__subspecies_of=None,
        ).values("parent__name", "desc")
    }
    db_records = [
        {"name": s["name"], "speed_text": speed_by_name.get(s["name"], "")}
        for s in Species.objects.filter(
            document_id=document, subspecies_of=None
        ).values("name")
    ]
    return compare_records("species", pdf_records, db_records, SKIP_FIELDS["species"])


# "items" (adventuring gear) is not in _RUNNERS because the SRD adventuring gear
# items do not have a dedicated model in api_v2 that maps cleanly to PDF records.
_RUNNERS = {
    "spells": _run_spell_comparison,
    "creatures": _run_creature_comparison,
    "weapons": _run_weapon_comparison,
    "armor": _run_armor_comparison,
    "magic_items": _run_magic_item_comparison,
    "classes": _run_class_comparison,
    "feats": _run_feat_comparison,
    "species": _run_species_comparison,
}


# ---------------------------------------------------------------------------
# Rich rendering
# ---------------------------------------------------------------------------


def _fmt_desc(value: Any, ratio: float | None = None, context: str = "") -> str:
    """Format a description value for Rich terminal display.

    Shows word count (more meaningful than char count for truncation), the
    word-level similarity ratio, and — when available — the context string
    from _desc_diff_context showing where the two versions diverge.
    """
    s = str(value) if value else ""
    if not s:
        return "(empty)"
    words = _to_word_tokens(_normalize_desc(s))
    ratio_str = f" [{ratio:.0%}]" if ratio is not None else ""
    suffix = f"\n{context}" if context else ""
    return f"{len(words)} words{ratio_str}{suffix}"


def _render_results(results: dict[str, ComparisonResult], elapsed: float) -> None:
    console = Console()

    def _fmt(n):
        return "[green]0[/green]" if n == 0 else str(n)

    summary = Table(title=f"SRD 5.2 PDF vs Database (completed in {elapsed:.1f}s)")
    summary.add_column("Entity type", style="bold")
    summary.add_column("In PDF", justify="right")
    summary.add_column("In DB", justify="right")
    summary.add_column("Missing", justify="right")
    summary.add_column("Extra", justify="right")
    summary.add_column("Mismatches", justify="right")
    summary.add_column("Desc mismatches", justify="right")

    for name, result in results.items():
        field_n = sum(1 for mm in result.mismatches if mm.field != "desc")
        desc_n = sum(1 for mm in result.mismatches if mm.field == "desc")
        summary.add_row(
            name,
            str(result.pdf_count),
            str(result.db_count),
            _fmt(len(result.missing)),
            _fmt(len(result.extra)),
            _fmt(field_n),
            _fmt(desc_n),
        )
    console.print(summary)

    for name, result in results.items():
        if result.missing:
            lines = []
            for n in result.missing:
                page = result.missing_pages.get(n, 0)
                suffix = f" (p. {page})" if page else ""
                lines.append(f"• {n}{suffix}")
            console.print(Panel(
                "\n".join(lines),
                title=f"Missing from DB — {name}",
                border_style="red",
            ))
        if result.extra:
            console.print(Panel(
                "\n".join(f"• {n}" for n in result.extra),
                title=f"Extra in DB — {name}",
                border_style="yellow",
            ))
        field_mm = [mm for mm in result.mismatches if mm.field != "desc"]
        desc_mm = [mm for mm in result.mismatches if mm.field == "desc"]

        if field_mm:
            t = Table(title=f"Field mismatches — {name}")
            t.add_column("Entity")
            t.add_column("Page", justify="right")
            t.add_column("Field")
            t.add_column("PDF value", style="green")
            t.add_column("DB value", style="red")
            for mm in field_mm:
                page_str = str(mm.page_number) if mm.page_number else "—"
                t.add_row(mm.entity_name, page_str, mm.field, str(mm.pdf_value), str(mm.db_value))
            console.print(t)

        if desc_mm:
            dt = Table(title=f"Description mismatches — {name}")
            dt.add_column("Entity")
            dt.add_column("Page", justify="right")
            dt.add_column("Type")
            dt.add_column("PDF words [sim]", style="green")
            dt.add_column("Context", style="yellow")
            dt.add_column("DB words", style="red")
            for mm in desc_mm:
                page_str = str(mm.page_number) if mm.page_number else "—"
                _, ratio = _compare_desc(mm.pdf_value or "", mm.db_value or "")
                ctx = _desc_diff_context(mm.pdf_value or "", mm.db_value or "")
                pdf_words = _to_word_tokens(_normalize_desc(mm.pdf_value or ""))
                db_words = _to_word_tokens(_normalize_desc(
                    _strip_markdown(mm.db_value or "")
                ))
                pdf_disp = f"{len(pdf_words)} [{ratio:.0%}]"
                db_disp = str(len(db_words))
                dt.add_row(mm.entity_name, page_str, mm.subtype or "—", pdf_disp, ctx, db_disp)
            console.print(dt)


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------


def _md_cell(value: Any) -> str:
    """Escape a value for use in a GitHub Markdown table cell (single line)."""
    return str(value).replace("|", "\\|").replace("\n", " ").replace("\r", "")


def _fmt_desc_md(value: Any, ratio: float | None = None, context: str = "") -> str:
    """Format a description value for a markdown table cell.

    Shows word count, word-level similarity ratio, and diff context.
    """
    s = str(value) if value else ""
    if not s:
        return "(empty)"
    words = _to_word_tokens(_normalize_desc(s))
    ratio_str = f", {ratio:.0%} similar" if ratio is not None else ""
    ctx_str = f" — {_md_cell(context)}" if context else ""
    return f"{len(words)} words{ratio_str}{ctx_str}"


def _render_markdown(results: dict[str, ComparisonResult], elapsed: float) -> None:
    """Render comparison results as GitHub-flavoured markdown to stdout."""
    out: list[str] = []

    out.append(f"## SRD 5.2 PDF vs Database\n")
    out.append("| Entity | In PDF | In DB | Missing | Extra | Mismatches | Desc mismatches |")
    out.append("|--------|-------:|------:|--------:|------:|-----------:|----------------:|")
    for name, result in results.items():
        field_n = sum(1 for mm in result.mismatches if mm.field != "desc")
        desc_n = sum(1 for mm in result.mismatches if mm.field == "desc")
        out.append(
            f"| {name} | {result.pdf_count} | {result.db_count}"
            f" | {len(result.missing)} | {len(result.extra)}"
            f" | {field_n} | {desc_n} |"
        )
    out.append("")

    for name, result in results.items():
        if result.missing:
            out.append(f"### Missing from DB — {name}\n")
            for n in result.missing:
                page = result.missing_pages.get(n, 0)
                suffix = f" (p. {page})" if page else ""
                out.append(f"- {n}{suffix}")
            out.append("")

        if result.extra:
            out.append(f"### Extra in DB — {name}\n")
            for n in result.extra:
                out.append(f"- {n}")
            out.append("")

        field_mm = [mm for mm in result.mismatches if mm.field != "desc"]
        desc_mm = [mm for mm in result.mismatches if mm.field == "desc"]

        if field_mm:
            out.append(f"### Field mismatches — {name}\n")
            out.append("| Entity | Page | Field | PDF value | DB value |")
            out.append("|--------|------|-------|-----------|----------|")
            for mm in field_mm:
                page_str = str(mm.page_number) if mm.page_number else "—"
                out.append(
                    f"| {_md_cell(mm.entity_name)} | {page_str}"
                    f" | {mm.field} | {_md_cell(mm.pdf_value)} | {_md_cell(mm.db_value)} |"
                )
            out.append("")

        if desc_mm:
            out.append(f"### Description mismatches — {name}\n")
            out.append("| Entity | Page | Type | PDF words | Similarity | Context | DB words |")
            out.append("|--------|------|------|----------:|-----------:|---------|--------:|")
            for mm in desc_mm:
                page_str = str(mm.page_number) if mm.page_number else "—"
                _, ratio = _compare_desc(mm.pdf_value or "", mm.db_value or "")
                ctx = _desc_diff_context(mm.pdf_value or "", mm.db_value or "")
                pdf_words = _to_word_tokens(_normalize_desc(mm.pdf_value or ""))
                db_words = _to_word_tokens(_normalize_desc(
                    _strip_markdown(mm.db_value or "")
                ))
                out.append(
                    f"| {_md_cell(mm.entity_name)} | {page_str}"
                    f" | {mm.subtype or '—'} | {len(pdf_words)} | {ratio:.0%}"
                    f" | {_md_cell(ctx)} | {len(db_words)} |"
                )
            out.append("")

    print("\n".join(out))


# ---------------------------------------------------------------------------
# Command
# ---------------------------------------------------------------------------

DEFAULT_PDF = os.path.normpath(os.path.join(
    os.path.dirname(__file__),
    "../../../data/raw_sources/srd_5_2/SRD_CC_v5.2.pdf",
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
        parser.add_argument(
            "--format",
            choices=["terminal", "markdown"],
            default="terminal",
            dest="output_format",
            help="Output format: terminal (default, Rich-formatted) or markdown "
                 "(GitHub-flavoured markdown suitable for pasting into issues).",
        )

    def handle(self, *args, **options):
        pdf_path = options["pdf"]
        document = options["document"]
        entity = options["entity"]
        output_format = options["output_format"]

        if not os.path.exists(pdf_path):
            raise CommandError(f"PDF not found: {pdf_path}")

        entity_types = list(_RUNNERS.keys()) if entity == "all" else [entity]

        start = time.monotonic()
        results: dict[str, ComparisonResult] = {}

        failed: list[str] = []

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
                    self.stderr.write(traceback.format_exc())
                    failed.append(etype)

        if failed:
            raise CommandError(f"Comparisons failed for: {', '.join(failed)}")

        elapsed = time.monotonic() - start
        ordered = {k: results[k] for k in entity_types if k in results}
        if output_format == "markdown":
            _render_markdown(ordered, elapsed)
        else:
            _render_results(ordered, elapsed)
