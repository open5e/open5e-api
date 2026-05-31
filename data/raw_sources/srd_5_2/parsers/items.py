"""Extract weapon, armor, and magic item records from SRD PDF text.

Two strategies per item type:
- extract_*(text): parse pre-extracted text (unit tests, raises on 0 records)
- extract_*_from_pdf(pdf_path): font-aware extraction from the real PDF with
  production-grade sanity checks (≥30 weapons, ≥10 armor, ≥200 magic items).

PDF layout notes (SRD 5.2):
- Weapons/Armor: single-column tables on pages 91–92 (plain text extraction works)
- Magic Items: two-column layout pages 209–250. Item names use GillSans-SemiBold
  size=12.0; rarity lines use Cambria-Italic. Font-aware extraction separates them
  cleanly, processing each column independently.
"""
from __future__ import annotations
import dataclasses
import re
from dataclasses import dataclass
import pdfplumber

from .base import clean_text, parse_dice, extract_section

# ---------------------------------------------------------------------------
# Section boundary patterns
# ---------------------------------------------------------------------------

_WEAPONS_START_RE = re.compile(r"^Weapons\s*$", re.MULTILINE)
_WEAPONS_END_RE = re.compile(r"^Armor\s*$", re.MULTILINE)

_ARMOR_START_RE = re.compile(r"^Armor\s*$", re.MULTILINE)
_ARMOR_END_RE = re.compile(r"^Tools\s*$", re.MULTILINE)

_MAGIC_ITEMS_START_RE = re.compile(r"^Magic Items\s+A(?:-|–)Z", re.IGNORECASE | re.MULTILINE)
_MAGIC_ITEMS_END_RE = re.compile(
    r"^(?:Monsters|Spells|Appendix|Chapter|Index|Part\s+\d|Rules\s+Glossary)",
    re.IGNORECASE | re.MULTILINE,
)

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class WeaponRecord:
    """A single weapon entry parsed from the SRD weapons table."""

    name: str
    cost: dict | None
    damage: dict | None   # None for flat-damage weapons like Blowgun ("1 Piercing")
    damage_type: str      # "piercing", "slashing", "bludgeoning"


@dataclass(frozen=True)
class ArmorRecord:
    """A single armor entry parsed from the SRD armor table."""

    name: str
    cost: dict | None
    ac_base: int
    ac_add_dex: bool
    ac_cap_dex: int | None
    strength_required: int | None
    stealth_disadvantage: bool


@dataclass(frozen=True)
class MagicItemRecord:
    """A single magic item entry parsed from the SRD magic items section."""

    name: str
    # Enchantment name: the magical property, with bonus-variant suffix stripped.
    # For unique items this equals name. For items like "Weapon, +1, +2, or +3"
    # the enchantment_name is "Weapon" — the property that can be applied to any weapon.
    enchantment_name: str
    rarity: str            # "common", "uncommon", "rare", "very rare", "legendary", "artifact"
    requires_attunement: bool
    page_number: int = 0  # PDF page where the item entry starts (0 = unknown)
    desc: str = ""        # body description text extracted from the same column


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_COST_RE = re.compile(
    r"([\d,]+(?:\.\d+)?)\s*(GP|SP|CP)\s*$", re.IGNORECASE
)

_RARITY_RE = re.compile(
    r"\b(very\s+rare|uncommon|common|legendary|artifact|rare)\b", re.IGNORECASE
)
_ATTUNEMENT_RE = re.compile(r"requires\s+attunement", re.IGNORECASE)
# Strips ", +1, +2, or +3" style bonus-variant suffixes to derive enchantment_name.
# Matches optional leading comma, then one or more "+N" items optionally joined by ", or +N".
_BONUS_VARIANT_RE = re.compile(
    r",?\s*\+\d+(?:\s*,\s*\+\d+)*(?:\s*,?\s*or\s+\+\d+)?\s*$"
)


# ---------------------------------------------------------------------------
# Weapon parsing
# ---------------------------------------------------------------------------

# Sub-section header lines to skip (not weapon entries)
_WEAPON_SKIP_RE = re.compile(
    r"^(?:Name(?:\s+Damage)?\b|Simple\s+(?:Melee|Ranged)|Martial\s+(?:Melee|Ranged))",
    re.IGNORECASE,
)

_DAMAGE_TYPE_RE = re.compile(
    r"\b(Bludgeoning|Piercing|Slashing)\b", re.IGNORECASE
)


def _parse_weapon_line(line: str) -> WeaponRecord | None:
    """Parse a single weapon table line into a WeaponRecord.

    Line format: Name [damage] DamageType [properties] Mastery Weight Cost
    Example: "Dagger 1d4 Piercing Finesse, Light, Thrown (Range 20/60) Nick 1 lb. 2 GP"
    Example: "Blowgun 1 Piercing Ammunition (Range 25/100; Needle), Loading Vex 1 lb. 10 GP"
    """
    line = clean_text(line)
    if not line or _WEAPON_SKIP_RE.match(line):
        return None

    # Find the damage type (Bludgeoning/Piercing/Slashing) — it's the anchor
    dm = _DAMAGE_TYPE_RE.search(line)
    if not dm:
        return None

    damage_type = dm.group(1).lower()
    before_type = line[: dm.start()].strip()

    # Find cost at the end of the line
    cost_m = _COST_RE.search(line)
    if not cost_m:
        return None
    amount_str = cost_m.group(1).replace(",", "")
    cost = {"amount": float(amount_str), "unit": cost_m.group(2).lower()}

    # `before_type`: "Name dice_or_number"
    # Try dice expression first ("1d4", "2d6"), then flat number ("1" for Blowgun)
    dice_m = re.search(r"(\d+[dD]\d+(?:[+-]\d+)?)$", before_type)
    if dice_m:
        damage = parse_dice(dice_m.group(1))
        name = before_type[: dice_m.start()].strip()
    else:
        flat_m = re.search(r"\s+(\d+)\s*$", before_type)
        if not flat_m:
            return None
        damage = None  # flat damage — not expressed as dice
        name = before_type[: flat_m.start()].strip()

    if not name or not name[0].isupper() or len(name) > 40:
        return None

    return WeaponRecord(name=name, cost=cost, damage=damage, damage_type=damage_type)


def extract_weapons(full_text: str) -> list[WeaponRecord]:
    """Parse weapon records from extracted text.

    Unit-test helper. Raises ValueError("found no weapons") when 0 records found.
    For production, use extract_weapons_from_pdf() which enforces ≥30.
    """
    try:
        section = extract_section(full_text, _WEAPONS_START_RE, _WEAPONS_END_RE)
    except ValueError:
        section = full_text

    records: list[WeaponRecord] = []
    seen: set[str] = set()
    for line in section.splitlines():
        rec = _parse_weapon_line(line)
        if rec and rec.name not in seen:
            seen.add(rec.name)
            records.append(rec)

    if not records:
        raise ValueError("found no weapons in the provided text")
    return records


def extract_weapons_from_pdf(pdf_path: str) -> list[WeaponRecord]:
    """Extract weapons from the real SRD PDF. Raises ValueError if fewer than 30 found."""
    from .base import extract_full_text  # deferred import
    full_text = extract_full_text(pdf_path)
    records = extract_weapons(full_text)
    if len(records) < 30:
        raise ValueError(
            f"Weapon parser produced only {len(records)} weapons — expected ≥30."
        )
    return records


# ---------------------------------------------------------------------------
# Armor parsing
# ---------------------------------------------------------------------------

_ARMOR_SKIP_RE = re.compile(
    r"^(?:Armor\s+Armor\s+Class|Light\s+Armor\s*\(|Medium\s+Armor\s*\(|"
    r"Heavy\s+Armor\s*\(|Shield\s*[(\+]|Shield\s+\()",
    re.IGNORECASE,
)

_DEX_AC_RE = re.compile(
    r"^(.+?)\s+(\d+)\s*\+\s*Dex\s+modifier(?:\s+\(max\s+(\d+)\))?",
    re.IGNORECASE,
)
_FLAT_AC_RE = re.compile(
    r"^(.+?)\s+(\d+)\s+(?:Str\s+(\d+)|—)",
    re.IGNORECASE,
)


def _parse_armor_line(line: str) -> ArmorRecord | None:
    """Parse a single armor table line into an ArmorRecord.

    Light/Medium: "Name 11 + Dex modifier — — weight cost"
                  "Name 13 + Dex modifier (max 2) — — weight cost"
    Heavy:        "Name 16 Str 13 Disadvantage weight cost"
                  "Name 14 — Disadvantage weight cost"
    """
    line = clean_text(line)
    if not line or _ARMOR_SKIP_RE.match(line):
        return None

    # Vehicle table rows always contain a speed ("mph"); armor rows never do.
    if "mph" in line:
        return None

    # Skip shield entry ("+2 — — ...")
    if line.startswith("+"):
        return None

    cost_m = _COST_RE.search(line)
    if not cost_m:
        return None
    amount_str = cost_m.group(1).replace(",", "")
    cost = {"amount": float(amount_str), "unit": cost_m.group(2).lower()}

    stealth_disadvantage = "Disadvantage" in line

    # Light / Medium armor: has "+ Dex modifier"
    dex_m = _DEX_AC_RE.match(line)
    if dex_m:
        name = clean_text(dex_m.group(1))
        ac_base = int(dex_m.group(2))
        ac_cap_dex = int(dex_m.group(3)) if dex_m.group(3) else None
        return ArmorRecord(
            name=name,
            cost=cost,
            ac_base=ac_base,
            ac_add_dex=True,
            ac_cap_dex=ac_cap_dex,
            strength_required=None,
            stealth_disadvantage=stealth_disadvantage,
        )

    # Heavy armor: flat AC, optionally "Str N"
    flat_m = _FLAT_AC_RE.match(line)
    if flat_m:
        name = clean_text(flat_m.group(1))
        if not name or not name[0].isupper() or len(name) > 40:
            return None
        return ArmorRecord(
            name=name,
            cost=cost,
            ac_base=int(flat_m.group(2)),
            ac_add_dex=False,
            ac_cap_dex=None,
            strength_required=int(flat_m.group(3)) if flat_m.group(3) else None,
            stealth_disadvantage=stealth_disadvantage,
        )

    return None


def extract_armor(full_text: str) -> list[ArmorRecord]:
    """Parse armor records from extracted text.

    Unit-test helper. Raises ValueError("found no armor") when 0 records found.
    For production, use extract_armor_from_pdf() which enforces ≥10.
    """
    try:
        section = extract_section(full_text, _ARMOR_START_RE, _ARMOR_END_RE)
    except ValueError:
        section = full_text

    records: list[ArmorRecord] = []
    seen: set[str] = set()
    for line in section.splitlines():
        rec = _parse_armor_line(line)
        if rec and rec.name not in seen:
            seen.add(rec.name)
            records.append(rec)

    if not records:
        raise ValueError("found no armor in the provided text")
    return records


def extract_armor_from_pdf(pdf_path: str) -> list[ArmorRecord]:
    """Extract armor from the real SRD PDF. Raises ValueError if fewer than 10 found."""
    from .base import extract_full_text  # deferred import
    full_text = extract_full_text(pdf_path)
    records = extract_armor(full_text)
    if len(records) < 10:
        raise ValueError(
            f"Armor parser produced only {len(records)} armor entries — expected ≥10."
        )
    return records


# ---------------------------------------------------------------------------
# Magic item parsing — font-aware, column-aware (two-column layout)
# ---------------------------------------------------------------------------

# Font identifiers in the SRD 5.2 PDF
_MI_NAME_FONT = "GillSans-SemiBold"
_MI_NAME_SIZE = 12.0
_MI_NAME_SIZE_TOL = 0.6
_MI_RARITY_FONT = "Cambria-Italic"


def _is_magic_item_name_char(char: dict) -> bool:
    """Return True if this PDF character belongs to a magic item name."""
    fontname = char.get("fontname", "")
    size = char.get("size", 0)
    return (
        _MI_NAME_FONT in fontname
        and "SC700" not in fontname
        and abs(size - _MI_NAME_SIZE) <= _MI_NAME_SIZE_TOL
    )


def _is_rarity_char(char: dict) -> bool:
    """Return True if this PDF character belongs to an italic rarity/type line."""
    return _MI_RARITY_FONT in char.get("fontname", "")


def _tagged_lines_for_col(chars: list[dict]) -> list[tuple[int, str, str]]:
    """Build ordered (y, text, tag) tagged lines from one column's characters.

    Tags: 'name' for magic-item-name font, 'rarity' for italic font,
    'body' for all remaining chars (the description text).
    Callers must pre-filter chars to a single column before calling.
    """
    line_map: dict[int, list[dict]] = {}
    for c in chars:
        y = round(c["top"])
        line_map.setdefault(y, []).append(c)

    tagged: list[tuple[int, str, str]] = []
    for y in sorted(line_map.keys()):
        line_chars = sorted(line_map[y], key=lambda c: c["x0"])
        name_chars = [c for c in line_chars if _is_magic_item_name_char(c)]
        rarity_chars = [c for c in line_chars if _is_rarity_char(c)]
        body_chars = [
            c for c in line_chars
            if not _is_magic_item_name_char(c) and not _is_rarity_char(c)
        ]

        if name_chars:
            text = "".join(c["text"] for c in name_chars).strip()
            if text:
                tagged.append((y, text, "name"))

        if rarity_chars:
            text = "".join(c["text"] for c in rarity_chars).strip()
            if text:
                tagged.append((y, text, "rarity"))

        if body_chars and not name_chars:
            text = "".join(c["text"] for c in body_chars).strip()
            if text:
                tagged.append((y, text, "body"))

    return tagged


def _pairs_from_tagged_lines(
    tagged_lines: list[tuple[int, str, str]],
) -> list[tuple[str, str, str]]:
    """Extract (name, rarity_line, desc) triples from an ordered list of tagged lines.

    Handles multi-line names (e.g., "Amulet of Proof against Detection" +
    "and Location") and multi-line rarity descriptions.  Body text lines
    that follow a rarity line (and precede the next item name) are joined
    as the description.
    """
    results: list[tuple[str, str, str]] = []
    i = 0
    while i < len(tagged_lines):
        y, text, tag = tagged_lines[i]
        if tag != "name":
            i += 1
            continue

        # Collect name continuation (next name line close in y = same item).
        # A single intervening 'body' line is allowed: the previous item's last
        # description sentence can land at a y-position between the two halves of
        # a multi-line name due to the PDF's two-column rendering order.
        name = text
        j = i + 1
        j_look = j
        if j_look < len(tagged_lines) and tagged_lines[j_look][2] == "body":
            j_look += 1  # skip one trailing body line from the previous item
        if j_look < len(tagged_lines) and tagged_lines[j_look][2] == "name":
            if abs(tagged_lines[j_look][0] - y) < 30:  # within ~30pts = wrapped line
                name = name + " " + tagged_lines[j_look][1]
                j = j_look + 1
        next_i = j

        # Find the next rarity line (skip any body text between name and rarity)
        rarity_text = ""
        while j < len(tagged_lines):
            if tagged_lines[j][2] == "rarity":
                rarity_text = tagged_lines[j][1]
                k = j + 1
                if k < len(tagged_lines) and tagged_lines[k][2] == "rarity":
                    rarity_text = rarity_text + " " + tagged_lines[k][1]
                    j = k
                break
            if tagged_lines[j][2] == "name":
                break  # hit next item before finding rarity — skip
            j += 1

        if not (rarity_text and _RARITY_RE.search(rarity_text)):
            i = next_i
            continue

        # Collect body lines after the rarity until the next item name
        j += 1
        desc_parts: list[str] = []
        while j < len(tagged_lines):
            t_tag = tagged_lines[j][2]
            if t_tag == "name":
                break
            if t_tag == "body":
                desc_parts.append(tagged_lines[j][1])
            j += 1

        desc = clean_text(" ".join(desc_parts))
        results.append((name.strip(), rarity_text.strip(), desc))
        i = next_i

    return results


def _extract_magic_items_from_page(page) -> list[tuple[str, str, str]]:
    """Extract (name, rarity_line, desc) triples from a single PDF page.

    Processes left and right columns independently to prevent cross-column
    name merges in the two-column layout.
    """
    chars = page.chars
    if not chars:
        return []

    page_mid = float(page.width) / 2.0
    results: list[tuple[str, str, str]] = []
    for left_col in (True, False):
        col_chars = [c for c in chars if (c["x0"] < page_mid - 2) is left_col]
        tagged = _tagged_lines_for_col(col_chars)
        results.extend(_pairs_from_tagged_lines(tagged))

    return results


def _parse_magic_item_pair(
    name: str, rarity_line: str, desc: str = ""
) -> MagicItemRecord | None:
    """Build a MagicItemRecord from a (name, rarity_line, desc) triple."""
    name = clean_text(name)
    if not name:
        return None
    m = _RARITY_RE.search(rarity_line)
    if not m:
        return None
    rarity = m.group(1).lower()
    # Normalise "very  rare" → "very rare" (extra space from PDF join)
    rarity = re.sub(r"\s+", " ", rarity)
    requires_attunement = bool(_ATTUNEMENT_RE.search(rarity_line))
    enchantment_name = _BONUS_VARIANT_RE.sub("", name).strip()
    return MagicItemRecord(
        name=name,
        enchantment_name=enchantment_name,
        rarity=rarity,
        requires_attunement=requires_attunement,
        desc=desc,
    )


def extract_magic_items(full_text: str) -> list[MagicItemRecord]:
    """Parse magic item records from pre-extracted single-column text.

    Unit-test helper. Uses a text heuristic: scan for a line immediately followed
    by a line containing a rarity keyword. Raises ValueError("found no magic items")
    when 0 records found.

    For production use (real PDF, two-column layout), call extract_magic_items_from_pdf().
    """
    try:
        section = extract_section(full_text, _MAGIC_ITEMS_START_RE, _MAGIC_ITEMS_END_RE)
    except ValueError:
        section = full_text

    non_empty = [(pos, ln) for pos, ln in enumerate(section.splitlines()) if ln.strip()]

    records: list[MagicItemRecord] = []
    seen: set[str] = set()
    i = 0
    while i < len(non_empty):
        _, line = non_empty[i]
        if i + 1 < len(non_empty):
            _, next_line = non_empty[i + 1]
            if _RARITY_RE.search(next_line):
                rec = _parse_magic_item_pair(line, next_line)
                if rec and rec.name not in seen:
                    seen.add(rec.name)
                    records.append(rec)
                i += 2
                continue
            # Multi-line name: line i+1 is a name continuation, line i+2 has the rarity
            if i + 2 < len(non_empty) and not _RARITY_RE.search(next_line):
                _, rarity_line = non_empty[i + 2]
                if _RARITY_RE.search(rarity_line):
                    combined_name = line.strip() + " " + next_line.strip()
                    rec = _parse_magic_item_pair(combined_name, rarity_line)
                    if rec and rec.name not in seen:
                        seen.add(rec.name)
                        records.append(rec)
                    i += 3
                    continue
        i += 1

    if not records:
        raise ValueError("found no magic items in the provided text")
    return records


def _is_magic_items_section_heading(page) -> bool:
    """Return True if this page carries the Magic Items A–Z section heading.

    Uses font-aware detection: the heading is GillSans-SemiBold at size ≈18.
    Text-only matching is unreliable ("Magic Items" appears in the TOC and body).
    """
    size18_chars = [
        c for c in page.chars
        if "GillSans-SemiBold" in c.get("fontname", "")
        and abs(c.get("size", 0) - 18.0) < 1.0
    ]
    if not size18_chars:
        return False
    text = "".join(c["text"] for c in sorted(size18_chars, key=lambda c: (c["top"], c["x0"])))
    return bool(re.search(r"Magic Items", text, re.IGNORECASE))


def _is_monsters_section_start(page) -> bool:
    """Return True if this page starts the Monsters section (signals end of magic items)."""
    first_line = (page.extract_text() or "").strip().split("\n")[0]
    return bool(re.match(r"Monsters\b", first_line, re.IGNORECASE))


def extract_magic_items_from_pdf(pdf_path: str) -> list[MagicItemRecord]:
    """Font-aware, column-aware magic item extraction from the real SRD PDF.

    Section start: page whose size-18 GillSans-SemiBold chars spell "Magic Items".
    Section end: first page whose first text line starts with "Monsters".

    Raises ValueError if fewer than 200 magic items are found (the SRD 5.2 PDF
    contains ~237 named item entries in the Magic Items A–Z section).
    """
    records: list[MagicItemRecord] = []
    seen: set[str] = set()

    with pdfplumber.open(pdf_path) as pdf:
        in_section = False
        for page in pdf.pages:
            page_num: int = page.page_number
            if not in_section:
                if _is_magic_items_section_heading(page):
                    in_section = True
            if not in_section:
                continue
            if _is_monsters_section_start(page):
                break

            for name, rarity_line, desc in _extract_magic_items_from_page(page):
                if name in seen:
                    continue
                rec = _parse_magic_item_pair(name, rarity_line, desc)
                if rec:
                    seen.add(rec.name)
                    records.append(dataclasses.replace(rec, page_number=page_num))

    if len(records) < 200:
        raise ValueError(
            f"Magic item parser produced only {len(records)} items — expected ≥200. "
            "Check section boundary detection and font extraction."
        )
    return records
