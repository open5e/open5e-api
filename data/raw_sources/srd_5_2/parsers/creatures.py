"""Extract creature records from SRD PDF text.

Two strategies:
- extract_creatures(text): parse pre-extracted single-column text (unit tests)
- extract_creatures_from_pdf(pdf_path): font-aware, column-aware extraction from the real PDF
"""
from __future__ import annotations
import re
from dataclasses import dataclass
import pdfplumber

from .base import clean_text, extract_section

# Section boundaries
_SECTION_START_RE = re.compile(r"Monsters\s+A[-–Z]", re.IGNORECASE)
_SECTION_END_RE = re.compile(
    r"^(?:Appendix|Chapter|Index|Part\s+\d|Rules\s+Glossary)",
    re.IGNORECASE | re.MULTILINE,
)

SIZES = {"Tiny", "Small", "Medium", "Large", "Huge", "Gargantuan"}
_SIZES_PATTERN = "|".join(SIZES)

# Entry boundary: a line starting with a size word followed by a creature type
_HEADER_RE = re.compile(
    rf"^({_SIZES_PATTERN})\s+([\w][\w\s]*?)(?:\s*\([^)]+\))?\s*,\s*(.+?)$",
    re.MULTILINE | re.IGNORECASE,
)

_AC_RE = re.compile(r"\bAC\s+(\d+)")
_HP_RE = re.compile(r"\bHP\s+(\d+)")
_CR_RE = re.compile(r"\bCR\s+([\d/]+)")
_SPEED_RE = re.compile(r"\bSpeed\b(.+?)(?:\n|$)", re.IGNORECASE)

# Ability score lines come in three formats:
# 1. Spaced:   "Str 27 +8 +8 Dex 14 +2 +7 Con 25 +7 +12"
# 2. Compact:  "Str 27+8+8Dex 14+2+7Con 25+7+12"
# 3. Mixed-sign compact: "Int 6-22WIS 11+0+3Cha 12+1+1" — negative mod followed by
#    unsigned positive save produces "6-22" (the PDF omits the + on the save), which
#    would cause [+\-]\d+ to greedily consume "-22" instead of "-2".
# Fix: use [^a-zA-Z]* between ability keywords so MOD+SAVE are consumed together
# without needing to parse them individually.
_SCORE = r"(\d+)"
_ABILITY_STR_DEX_CON_RE = re.compile(
    rf"Str\s+{_SCORE}[^a-zA-Z]*"
    rf"Dex\s+{_SCORE}[^a-zA-Z]*"
    rf"Con\s+{_SCORE}",
    re.IGNORECASE,
)
_ABILITY_INT_WIS_CHA_RE = re.compile(
    rf"Int\s+{_SCORE}[^a-zA-Z]*"
    rf"Wis\s+{_SCORE}[^a-zA-Z]*"
    rf"Cha\s+{_SCORE}",
    re.IGNORECASE,
)

_DAMAGE_IMMUNITIES_RE = re.compile(
    r"Damage\s+Immunities\s+(.+?)(?:\n|$)", re.IGNORECASE
)
_DAMAGE_RESISTANCES_RE = re.compile(
    r"Damage\s+Resistances\s+(.+?)(?:\n|$)", re.IGNORECASE
)
_DAMAGE_VULNERABILITIES_RE = re.compile(
    r"Damage\s+Vulnerabilities\s+(.+?)(?:\n|$)", re.IGNORECASE
)
_CONDITION_IMMUNITIES_RE = re.compile(
    r"Condition\s+Immunities\s+(.+?)(?:\n|$)", re.IGNORECASE
)
_DARKVISION_RE = re.compile(r"Darkvision\s+(\d+)", re.IGNORECASE)
_BLINDSIGHT_RE = re.compile(r"Blindsight\s+(\d+)", re.IGNORECASE)
_TRUESIGHT_RE = re.compile(r"Truesight\s+(\d+)", re.IGNORECASE)

# Font identification for creature names in the SRD PDF
# Creature names use GillSans-SemiBold at size >= 14 (18 = section header, 15 = creature name)
_CREATURE_NAME_MIN_SIZE = 14.0
_CREATURE_NAME_FONT = "GillSans-SemiBold"
_CREATURE_NAME_SMALLCAPS_SUFFIX = "SC700"


@dataclass(frozen=True)
class CreatureRecord:
    name: str
    size: str
    type: str
    alignment: str
    armor_class: int
    hit_points: int
    hit_dice: str
    walk: int
    fly: int | None
    swim: int | None
    burrow: int | None
    climb: int | None
    hover: bool
    strength: int
    dexterity: int
    constitution: int
    intelligence: int
    wisdom: int
    charisma: int
    challenge_rating: float
    damage_immunities: tuple[str, ...]
    damage_resistances: tuple[str, ...]
    damage_vulnerabilities: tuple[str, ...]
    condition_immunities: tuple[str, ...]
    darkvision_range: int
    blindsight_range: int
    truesight_range: int


def _parse_cr(s: str) -> float:
    s = s.strip()
    if "/" in s:
        num, den = s.split("/")
        return int(num) / int(den)
    return float(s)


def _parse_speed(s: str) -> dict:
    result: dict = {
        "walk": 0,
        "fly": None,
        "swim": None,
        "burrow": None,
        "climb": None,
        "hover": False,
    }
    for part in s.split(","):
        part = clean_text(part.strip())
        m = re.search(r"(\d+)\s*ft", part, re.IGNORECASE)
        if not m:
            continue
        v = int(m.group(1))
        p = part.lower()
        if "fly" in p:
            result["fly"] = v
            if "hover" in p:
                result["hover"] = True
        elif "swim" in p:
            result["swim"] = v
        elif "burrow" in p:
            result["burrow"] = v
        elif "climb" in p:
            result["climb"] = v
        elif "(" not in p:
            # Skip form-specific walk speeds like "40 ft. (bear form only)";
            # the base walking speed (no qualifier) is listed first.
            result["walk"] = v
    return result


def _parse_list_field(m: re.Match | None) -> tuple[str, ...]:
    if not m:
        return ()
    raw = m.group(1)
    # Strip qualifiers after semicolon (e.g., "from nonmagical attacks")
    raw = raw.split(";")[0]
    return tuple(t.strip().lower() for t in raw.split(",") if t.strip())


def _normalize_block(block: str) -> str:
    """Normalize block text: replace Unicode minus (U+2212) with ASCII minus."""
    return block.replace("−", "-")


def _parse_block(name: str, block: str) -> CreatureRecord | None:
    """Parse a creature stat block given the name and the block text."""
    block = _normalize_block(block)

    header_m = _HEADER_RE.search(block)
    if not header_m:
        return None

    size = header_m.group(1).strip().title()
    creature_type = re.sub(r"\s*\([^)]+\)", "", header_m.group(2)).strip().lower()
    alignment = clean_text(header_m.group(3).strip())

    ac_m = _AC_RE.search(block)
    hp_m = _HP_RE.search(block)
    cr_m = _CR_RE.search(block)

    if not all([ac_m, hp_m, cr_m]):
        return None

    hd_m = re.search(r"HP\s+\d+\s*\(([^)]+)\)", block)
    hit_dice = hd_m.group(1).strip() if hd_m else ""

    speed_m = _SPEED_RE.search(block)
    speed = _parse_speed(speed_m.group(1)) if speed_m else {}

    str_dex_con_m = _ABILITY_STR_DEX_CON_RE.search(block)
    int_wis_cha_m = _ABILITY_INT_WIS_CHA_RE.search(block)

    str_ = int(str_dex_con_m.group(1)) if str_dex_con_m else 10
    dex_ = int(str_dex_con_m.group(2)) if str_dex_con_m else 10
    con_ = int(str_dex_con_m.group(3)) if str_dex_con_m else 10
    int_ = int(int_wis_cha_m.group(1)) if int_wis_cha_m else 10
    wis_ = int(int_wis_cha_m.group(2)) if int_wis_cha_m else 10
    cha_ = int(int_wis_cha_m.group(3)) if int_wis_cha_m else 10

    darkvision = int(dv.group(1)) if (dv := _DARKVISION_RE.search(block)) else 0
    blindsight = int(bs.group(1)) if (bs := _BLINDSIGHT_RE.search(block)) else 0
    truesight = int(ts.group(1)) if (ts := _TRUESIGHT_RE.search(block)) else 0

    return CreatureRecord(
        name=name,
        size=size,
        type=creature_type,
        alignment=alignment,
        armor_class=int(ac_m.group(1)),
        hit_points=int(hp_m.group(1)),
        hit_dice=hit_dice,
        walk=speed.get("walk", 0),
        fly=speed.get("fly"),
        swim=speed.get("swim"),
        burrow=speed.get("burrow"),
        climb=speed.get("climb"),
        hover=speed.get("hover", False),
        strength=str_,
        dexterity=dex_,
        constitution=con_,
        intelligence=int_,
        wisdom=wis_,
        charisma=cha_,
        challenge_rating=_parse_cr(cr_m.group(1)),
        damage_immunities=_parse_list_field(_DAMAGE_IMMUNITIES_RE.search(block)),
        damage_resistances=_parse_list_field(_DAMAGE_RESISTANCES_RE.search(block)),
        damage_vulnerabilities=_parse_list_field(
            _DAMAGE_VULNERABILITIES_RE.search(block)
        ),
        condition_immunities=_parse_list_field(
            _CONDITION_IMMUNITIES_RE.search(block)
        ),
        darkvision_range=darkvision,
        blindsight_range=blindsight,
        truesight_range=truesight,
    )


def extract_creatures(full_text: str) -> list[CreatureRecord]:
    """Parse creature records from extracted (single-column) text.

    Unit-test helper that parses pre-extracted single-column text.
    For the real PDF, use extract_creatures_from_pdf() which handles two-column
    layout and enforces a >=250 creature minimum.

    Raises ValueError("found no creatures") when zero records found.
    """
    full_text = _normalize_block(full_text)

    # Try to isolate the creature section; fall back to full text for unit tests
    try:
        section = extract_section(full_text, _SECTION_START_RE, _SECTION_END_RE)
    except ValueError:
        section = full_text

    # Find all header matches (size+type lines) — these are the entry boundaries
    header_matches = list(_HEADER_RE.finditer(section))
    records: list[CreatureRecord] = []
    seen_names: set[str] = set()

    for i, m in enumerate(header_matches):
        # The creature name is on the line immediately before the header match
        start = m.start()
        preceding = section[:start].rstrip()
        name_line = preceding.split("\n")[-1].strip()
        name = clean_text(name_line)

        # The block extends to where the next creature's name begins
        if i + 1 < len(header_matches):
            next_start = header_matches[i + 1].start()
            next_preceding = section[:next_start].rstrip()
            name_start = next_preceding.rfind("\n") + 1
            end = name_start
        else:
            end = len(section)

        block = section[start:end]

        # Sanity checks on the name
        if not name:
            continue
        if name in seen_names:
            continue
        if len(name) > 60:
            continue
        if name.lower().startswith(
            ("appendix", "chapter", "monsters", "index", "part ")
        ):
            continue

        record = _parse_block(name, block)
        if record:
            seen_names.add(name)
            records.append(record)

    if len(records) == 0:
        raise ValueError("found no creatures in the provided text")
    return records


# ---------------------------------------------------------------------------
# PDF extraction — font-aware, column-aware (handles two-column layout)
# ---------------------------------------------------------------------------


def _is_creature_name_char(char: dict) -> bool:
    """Return True if this PDF character is part of a creature name (by font)."""
    fontname = char.get("fontname", "")
    size = char.get("size", 0)
    return (
        _CREATURE_NAME_FONT in fontname
        and _CREATURE_NAME_SMALLCAPS_SUFFIX not in fontname
        and size >= _CREATURE_NAME_MIN_SIZE
    )


def _extract_column_blocks(page, left_col: bool) -> list[tuple[str, str]]:
    """Extract (name, block_text) pairs from one column of a PDF page.

    Uses character-level x-position filtering to separate columns, and font
    identification to locate creature name boundaries.

    Returns a list of (creature_name, block_text) tuples for creatures whose
    stat block starts in this column. Group-header names (no stat block) are
    returned with empty block text and filtered out later.
    """
    page_w = float(page.width)
    half = page_w / 2

    chars = page.chars
    if left_col:
        col_chars = [c for c in chars if c["x0"] < half - 2]
    else:
        col_chars = [c for c in chars if c["x0"] >= half - 2]

    if not col_chars:
        return []

    col_chars.sort(key=lambda c: (c["top"], c["x0"]))

    # Group chars into lines by y-proximity (within 4 pts = same line)
    lines: list[tuple[float, str, bool, float]] = []  # (y, text, is_name, max_size)
    i = 0
    while i < len(col_chars):
        y0 = col_chars[i]["top"]
        line_chars = []
        while i < len(col_chars) and abs(col_chars[i]["top"] - y0) <= 4:
            line_chars.append(col_chars[i])
            i += 1

        name_chars = [c for c in line_chars if _is_creature_name_char(c)]
        other_chars = [c for c in line_chars if not _is_creature_name_char(c)]

        if name_chars:
            name_chars.sort(key=lambda c: c["x0"])
            name_text = "".join(c["text"] for c in name_chars).strip()
            max_name_size = max(c["size"] for c in name_chars)
            if name_text:
                lines.append((y0, name_text, True, max_name_size))

        if other_chars:
            other_chars.sort(key=lambda c: c["x0"])
            other_text = "".join(c["text"] for c in other_chars).strip()
            if other_text:
                lines.append((y0 + 0.001, other_text, False, 0.0))

    # Split into blocks at each creature name line.
    # The PDF often emits the same name twice: once at size 18 (group heading) and
    # once at size 15 (stat-block subheading, sometimes with spaces removed, e.g.
    # "GrayOoze" instead of "Gray Ooze"). We track the last size-18 name so we can
    # restore it when the size-15 version is a space-stripped duplicate.
    blocks: list[tuple[str, str]] = []
    current_name: str | None = None
    current_lines: list[str] = []
    last_large_name: str | None = None  # most recent size >= 17 name

    for _y, text, is_name, max_size in lines:
        if is_name:
            # Skip the section header "Monsters A–Z"
            if _SECTION_START_RE.search(text):
                continue

            # Restore spaces if this is a compressed duplicate of a large name
            # e.g. "GrayOoze" -> "Gray Ooze" when last_large_name == "Gray Ooze"
            resolved_name = text
            if (
                max_size < 17
                and last_large_name is not None
                and text.replace(" ", "") == last_large_name.replace(" ", "")
                and text != last_large_name
            ):
                resolved_name = last_large_name

            if max_size >= 17:
                last_large_name = text

            # Start a new block
            if current_name is not None:
                blocks.append((current_name, "\n".join(current_lines)))
            current_name = resolved_name
            current_lines = [resolved_name]
        else:
            if current_name is not None:
                current_lines.append(text)

    if current_name is not None:
        blocks.append((current_name, "\n".join(current_lines)))

    return blocks


def extract_creatures_from_pdf(pdf_path: str) -> list[CreatureRecord]:
    """Font-aware, column-aware creature extraction from the SRD PDF.

    Uses character x-position filtering and font name detection to:
    1. Separate left and right columns precisely
    2. Identify creature name boundaries via font (GillSans-SemiBold size>=14)
    3. Parse each creature block

    Raises ValueError if fewer than 250 creatures are found.
    """
    all_blocks: list[tuple[str, str]] = []

    with pdfplumber.open(pdf_path) as pdf:
        in_creature_section = False
        for page in pdf.pages:
            full_page_text = page.extract_text() or ""
            if not in_creature_section:
                if _SECTION_START_RE.search(full_page_text):
                    in_creature_section = True
            if not in_creature_section:
                continue
            # Creatures run to end of PDF — no end boundary

            for left_col in (True, False):
                col_blocks = _extract_column_blocks(page, left_col=left_col)
                all_blocks.extend(col_blocks)

    records: list[CreatureRecord] = []
    seen_names: set[str] = set()

    for name, block in all_blocks:
        # Skip duplicate names (same creature appears at size-18 heading and
        # size-15 stat block; take the first occurrence that has a valid stat block)
        if name in seen_names:
            continue
        # Normalize and try to parse
        block_normalized = _normalize_block(block)
        record = _parse_block(name, block_normalized)
        if record:
            seen_names.add(name)
            records.append(record)

    if len(records) < 250:
        raise ValueError(
            f"Creature parser produced only {len(records)} creatures — expected ≥250. "
            "Check section boundary detection and column/font extraction."
        )
    return records
