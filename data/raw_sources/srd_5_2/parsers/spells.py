"""Extract spell records from SRD PDF text.

Two strategies:
- extract_spells(text): parse pre-extracted single-column text (used by unit tests)
- extract_spells_from_pdf(pdf_path): font-aware, column-aware extraction from the real PDF
  (used by the management command, handles two-column layout)

Font taxonomy for this PDF (SRD 5.2):
  GillSans-SemiBold size=12     -> spell names (standard)
  GillSans-SemiBold-SC700       -> spell names in small caps (e.g. "Acid Splash")
  Cambria-Italic size=10        -> level/school line ("Level 2 Evocation (Wizard)")
  GillSans-SemiBold size=9.5    -> field labels ("Casting Time:", "Range:", ...)
  BOKFGA+GillSans / GillSans    -> field values ("Action", "90 feet", ...)
  Cambria size=10               -> body text
  Cambria-BoldItalic size=10    -> "Using a Higher-Level Spell Slot." header
"""
from __future__ import annotations
import re
from dataclasses import dataclass
import pdfplumber

from .base import clean_text, extract_section

# Section boundaries in the PDF text
_SECTION_START_RE = re.compile(r"Spell Descriptions", re.IGNORECASE)
_SECTION_END_RE = re.compile(
    r"^(?:Appendix|Chapter|Glossary|Index|Part\s+\d|Rules Glossary)",
    re.IGNORECASE | re.MULTILINE,
)

SCHOOLS = {
    "abjuration", "conjuration", "divination", "enchantment",
    "evocation", "illusion", "necromancy", "transmutation",
}

_FIELD_RE = re.compile(
    r"^(Casting Time|Range|Components|Duration):\s*(.+)$", re.MULTILINE
)
_HIGHER_LEVEL_RE = re.compile(
    r"(?:At Higher Levels|Using a Higher-Level Spell Slot)[.\s]*(.+?)(?=\n\n|\Z)",
    re.DOTALL,
)

# Font name fragments that identify spell name characters
_SPELL_NAME_FONTS = ("GillSans-SemiBold",)  # matches GillSans-SemiBold and GillSans-SemiBold-SC700
_SPELL_NAME_SIZE = 12.0  # spell name font size (standard bold) or SC700 (small caps)
_LEVEL_LINE_FONT = "Cambria-Italic"


def _is_level_school_line(line: str) -> bool:
    """Return True if the line looks like a spell level/school line."""
    line_lower = line.lower()
    has_school = any(school in line_lower for school in SCHOOLS)
    if not has_school:
        return False
    has_level = bool(re.search(r"Level\s+\d+", line, re.IGNORECASE))
    has_cantrip = "cantrip" in line_lower
    return has_level or has_cantrip


def _parse_level(level_line: str) -> int:
    """Return level from a level/school line.

    Handles: "Level 2 Evocation (Wizard)" -> 2
             "Evocation Cantrip (Wizard)" -> 0
    """
    line = level_line.strip()
    if "cantrip" in line.lower():
        return 0
    m = re.search(r"Level\s+(\d+)", line, re.IGNORECASE)
    if m:
        return int(m.group(1))
    return 0


def _parse_school(level_line: str) -> str:
    """Return lowercase school name from a level/school line."""
    line = level_line.lower()
    for school in SCHOOLS:
        if school in line:
            return school
    return ""


def _parse_components(components_str: str) -> tuple[bool, bool, bool, str | None]:
    """Parse 'V, S, M (description)' into (verbal, somatic, material, material_specified)."""
    before_paren = components_str.split("(")[0]
    verbal = bool(re.search(r"\bV\b", before_paren))
    somatic = bool(re.search(r"\bS\b", before_paren))
    material = bool(re.search(r"\bM\b", before_paren))
    mat_specified = None
    m = re.search(r"\((.+?)\)", components_str)
    if m:
        mat_specified = m.group(1).strip()
    return verbal, somatic, material, mat_specified


def _parse_block(block: str) -> "SpellRecord | None":
    """Parse a single spell block into a SpellRecord. Returns None if not a valid spell."""
    lines = [line.strip() for line in block.strip().splitlines() if line.strip()]
    if len(lines) < 3:
        return None

    name = clean_text(lines[0])
    # Validate: name must not look like a field or heading
    if ":" in name or name.lower() in {"ritual", "at higher levels"}:
        return None
    # Skip section headers
    if name.lower().startswith(("appendix", "chapter", "part ", "glossary", "index",
                                "rules glossary", "spell descriptions")):
        return None

    # Find level/school line (usually line 1, but may be line 2 if "Ritual" appears)
    level_line_idx = None
    for i, line in enumerate(lines[1:4], start=1):
        if _is_level_school_line(line):
            level_line_idx = i
            break
    if level_line_idx is None:
        return None

    level_line = lines[level_line_idx]
    level = _parse_level(level_line)
    school = _parse_school(level_line)
    if not school:
        return None

    # Check for ritual marker (standalone "Ritual" line or in casting time)
    ritual = any(line.strip().lower() == "ritual" for line in lines)
    if not ritual:
        ritual = bool(re.search(r"Casting Time.*Ritual|Ritual.*Casting Time|^Ritual$",
                                block, re.IGNORECASE | re.MULTILINE))

    fields: dict[str, str] = {}
    for fm in _FIELD_RE.finditer(block):
        fields[fm.group(1)] = fm.group(2).strip()

    if not fields.get("Casting Time"):
        return None

    components_str = fields.get("Components", "")
    verbal, somatic, material, mat_specified = _parse_components(components_str)

    duration_raw = fields.get("Duration", "")
    concentration = "concentration" in duration_raw.lower()

    hl_m = _HIGHER_LEVEL_RE.search(block)
    higher_level = clean_text(hl_m.group(1).strip()) if hl_m else None

    return SpellRecord(
        name=name,
        level=level,
        school=school,
        casting_time=fields.get("Casting Time", ""),
        range_text=fields.get("Range", ""),
        verbal=verbal,
        somatic=somatic,
        material=material,
        material_specified=mat_specified,
        duration=duration_raw,
        concentration=concentration,
        ritual=ritual,
        higher_level=higher_level,
    )


@dataclass(frozen=True)
class SpellRecord:
    name: str
    level: int        # 0 = cantrip
    school: str       # lowercase school name
    casting_time: str
    range_text: str
    verbal: bool
    somatic: bool
    material: bool
    material_specified: str | None
    duration: str
    concentration: bool
    ritual: bool
    higher_level: str | None


def extract_spells(full_text: str) -> list[SpellRecord]:
    """Parse spell records from extracted (single-column) text.

    Unit-test helper that parses pre-extracted single-column text.
    For the real PDF, use extract_spells_from_pdf() which handles two-column layout
    and enforces a ≥300 spell minimum.

    Raises ValueError if no spells are found (sanity check for empty input).
    """
    records = _extract_spells_no_check(full_text)
    if len(records) == 0:
        raise ValueError(
            "Spell parser found no spells in the provided text. "
            "For production use, call extract_spells_from_pdf() which enforces ≥300."
        )
    return records


def _extract_spells_no_check(full_text: str) -> list[SpellRecord]:
    """Internal: parse spell records without the count sanity check."""
    # Try to isolate the spell section; fall back to full text for unit tests
    try:
        section = extract_section(full_text, _SECTION_START_RE, _SECTION_END_RE)
    except ValueError:
        section = full_text

    # Split into candidate spell blocks on blank lines
    raw_blocks = re.split(r"\n\s*\n", section)

    records: list[SpellRecord] = []
    seen_names: set[str] = set()

    for block in raw_blocks:
        record = _parse_block(block)
        if record and record.name not in seen_names:
            seen_names.add(record.name)
            records.append(record)

    return records


def _is_spell_name_char(char: dict) -> bool:
    """Return True if this PDF character is part of a spell name (by font)."""
    fontname = char.get("fontname", "")
    size = char.get("size", 0)
    # Spell names use GillSans-SemiBold at size ~12 or GillSans-SemiBold-SC700 at size ~8-12
    if any(font in fontname for font in _SPELL_NAME_FONTS) and size >= 7.0:
        # Exclude field labels (GillSans-SemiBold at size 9.5) and page numbers (size 11)
        # Spell names are at size 12 (or 8.4 for SC700 small caps)
        if "SC700" in fontname:
            return True  # Small caps spell names (like "Acid Splash")
        # For regular GillSans-SemiBold, size must be ~12 (not 9.5 for labels or 11 for page#)
        # 7.0 is below SC700 body text (~8.4), above noise
        if size >= 11.5:
            return True
    return False


def _extract_column_chars_as_blocks(page, left_col: bool) -> list[str]:
    """Extract spell text blocks from one column of a PDF page using font-aware parsing.

    Uses character-level x-position filtering to separate columns cleanly,
    and font identification to locate spell name boundaries.

    Returns a list of text blocks, each starting with a spell name line.
    When the column starts mid-spell (no spell name boundary), returns the
    continuation text as a single block with no leading name.
    """
    page_w = float(page.width)
    half = page_w / 2

    chars = page.chars

    # Filter chars to this column only
    if left_col:
        col_chars = [c for c in chars if c["x0"] < half - 2]
    else:
        col_chars = [c for c in chars if c["x0"] >= half - 2]

    if not col_chars:
        return []

    # Sort by y then x
    col_chars.sort(key=lambda c: (c["top"], c["x0"]))

    # Group chars into lines by y-proximity (within 4 points = same line)
    # Then for each line group by font to separate spell names from body text
    lines: list[tuple[float, str, bool]] = []  # (y, text, is_spell_name)

    i = 0
    while i < len(col_chars):
        # Collect all chars at approximately the same y
        y0 = col_chars[i]["top"]
        line_chars = []
        while i < len(col_chars) and abs(col_chars[i]["top"] - y0) <= 4:
            line_chars.append(col_chars[i])
            i += 1

        # Check if any chars in this line are spell name font
        has_spell_name_chars = any(_is_spell_name_char(c) for c in line_chars)

        # If line has mixed fonts, separate them
        if has_spell_name_chars:
            # Extract only the spell-name-font chars from this line
            name_chars = [c for c in line_chars if _is_spell_name_char(c)]
            body_chars = [c for c in line_chars if not _is_spell_name_char(c)]

            # Build spell name text, handling SC700 small-caps casing
            name_chars.sort(key=lambda c: c["x0"])
            name_text = _reconstruct_name_from_chars(name_chars)

            if name_text:
                lines.append((y0, name_text, True))

            # Build body text for non-name chars on the same line
            if body_chars:
                body_chars.sort(key=lambda c: c["x0"])
                body_text = "".join(c["text"] for c in body_chars).strip()
                if body_text:
                    lines.append((y0 + 0.001, body_text, False))
        else:
            # All same type (body/level/field text)
            line_chars.sort(key=lambda c: c["x0"])
            text = "".join(c["text"] for c in line_chars).strip()
            if text:
                lines.append((y0, text, False))

    # Now split into blocks at each spell name line
    # A spell name line followed by what looks like a level line starts a new block
    blocks: list[str] = []
    current_block_lines: list[str] = []
    found_first_spell = False

    for j, (y, text, is_name) in enumerate(lines):
        if is_name:
            # Check if a level line appears within the next several lines
            # (there may be a "at higher levels" body-text line between the spell name
            # and the level line when a previous spell's body flows past the new name)
            next_is_level = False
            non_name_count = 0
            for k in range(j + 1, min(j + 8, len(lines))):
                if not lines[k][2]:  # not a name line
                    if _is_level_school_line(lines[k][1]):
                        next_is_level = True
                        break
                    non_name_count += 1
                    if non_name_count >= 3:
                        break  # too many body lines before level — not a real spell name here

            if next_is_level:
                # Start of a new spell
                if current_block_lines:
                    blocks.append("\n".join(current_block_lines))
                current_block_lines = [text]
                found_first_spell = True
            else:
                # Name-font text but not followed by level line — could be a section header
                # or a stat block header; append to current block
                current_block_lines.append(text)
        else:
            current_block_lines.append(text)

    if current_block_lines:
        blocks.append("\n".join(current_block_lines))

    return blocks


def _reconstruct_name_from_chars(name_chars: list[dict]) -> str:
    """Reconstruct a spell name from its chars, handling SC700 small-caps encoding.

    GillSans-SemiBold-SC700 uses two font sizes:
    - Large size (~12): actual uppercase letters (e.g. 'A', 'S' in "Acid Splash")
    - Small size (~8.4): lowercase letters rendered as small-caps glyphs, but
      pdfplumber may extract them as uppercase (e.g. 'A','S','h' for 'a','s','h')

    Sort all chars by x-position and convert small-size SC700 chars to lowercase.
    Non-SC700 name chars (regular GillSans-SemiBold) are kept as-is.
    """
    if not name_chars:
        return ""
    # Find max size among SC700 chars to determine threshold
    sc700_chars = [c for c in name_chars if "SC700" in c.get("fontname", "")]
    if sc700_chars:
        max_sc700_size = max(c["size"] for c in sc700_chars)
        threshold = max_sc700_size * 0.8
    else:
        threshold = 0  # no SC700 chars, threshold unused

    parts = []
    for c in name_chars:  # already sorted by x0
        if "SC700" in c.get("fontname", "") and c["size"] < threshold:
            parts.append(c["text"].lower())
        else:
            parts.append(c["text"])
    return "".join(parts).strip()


def extract_spells_from_pdf(pdf_path: str) -> list[SpellRecord]:
    """Font-aware, column-aware spell extraction from the SRD PDF.

    Uses character x-position filtering and font name detection to:
    1. Separate left and right columns precisely
    2. Identify spell name boundaries via font (GillSans-SemiBold size=12)
    3. Parse each spell block

    Raises ValueError if fewer than 300 spells are found.
    """
    all_blocks: list[str] = []

    with pdfplumber.open(pdf_path) as pdf:
        in_spell_section = False
        for page in pdf.pages:
            full_page_text = page.extract_text() or ""
            if not in_spell_section:
                if _SECTION_START_RE.search(full_page_text):
                    in_spell_section = True
            if not in_spell_section:
                continue
            if _SECTION_END_RE.search(full_page_text):
                break

            # Extract both columns separately using font-aware char extraction
            for left_col in (True, False):
                col_blocks = _extract_column_chars_as_blocks(page, left_col=left_col)
                all_blocks.extend(col_blocks)

    records: list[SpellRecord] = []
    seen_names: set[str] = set()
    for block in all_blocks:
        record = _parse_block(block)
        if record and record.name not in seen_names:
            seen_names.add(record.name)
            records.append(record)

    if len(records) < 300:
        raise ValueError(
            f"Spell parser produced only {len(records)} spells — expected ≥300. "
            "Check section boundary detection and column/font extraction."
        )
    return records
