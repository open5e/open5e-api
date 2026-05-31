"""Extract feat and species records from the SRD PDF Character Origins chapter."""
from __future__ import annotations
import re
from dataclasses import dataclass
import pdfplumber

from .base import clean_text


# ---------------------------------------------------------------------------
# Feats
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FeatRecord:
    """A single feat extracted from the SRD PDF."""

    name: str
    feat_type: str      # "Origin", "General", "Fighting Style", "Epic Boon"
    prerequisite: str   # empty string when none
    page_number: int = 0


# Real PDF font profile (verified against SRD CC v5.2):
#   sz=12 GillSans-SemiBold  → individual feat name  (e.g. "Alert")
#   sz=10 Cambria-Italic     → type tag line(s)       (e.g. "Origin Feat")
#   sz=14 GillSans-SemiBold  → group section header   (e.g. "Origin Feats") — skip
#   sz=26 GillSans-SemiBold  → chapter heading        (e.g. "Feats") — for page detection
_FEAT_NAME_FONT = "GillSans-SemiBold"
_FEAT_NAME_SIZE = 12.0

_FEAT_TAG_FONT = "Cambria-Italic"
_FEAT_TAG_SIZE = 10.0

_CHAPTER_FONT = "GillSans-SemiBold"
_CHAPTER_SIZE = 26.0

_FEAT_TYPE_RE = re.compile(
    r"^(Origin|General|Fighting Style|Epic Boon)\s+Feat"
    r"(?:\s*\(Prerequisite:\s*(.+)\))?",
    re.IGNORECASE,
)


def _char_is_feat_name(char: dict) -> bool:
    return (
        _FEAT_NAME_FONT in char.get("fontname", "")
        and abs(char.get("size", 0) - _FEAT_NAME_SIZE) < 0.5
    )


def _char_is_feat_tag(char: dict) -> bool:
    return (
        _FEAT_TAG_FONT in char.get("fontname", "")
        and abs(char.get("size", 0) - _FEAT_TAG_SIZE) < 0.5
    )


def _group_into_lines(chars: list[dict]) -> list[tuple[float, list[dict]]]:
    """Sort chars by (top, x0) and group into lines by y-proximity (≤4 pts)."""
    chars = sorted(chars, key=lambda c: (c["top"], c["x0"]))
    lines: list[tuple[float, list[dict]]] = []
    i = 0
    while i < len(chars):
        y0 = chars[i]["top"]
        group: list[dict] = []
        while i < len(chars) and abs(chars[i]["top"] - y0) <= 4:
            group.append(chars[i])
            i += 1
        lines.append((y0, group))
    return lines


def extract_feats(pages: list) -> list[FeatRecord]:
    """Extract FeatRecords from a list of pdfplumber page objects.

    Font-aware extraction verified against SRD CC v5.2:
      - Feat names:  GillSans-SemiBold sz=12
      - Type tags:   Cambria-Italic sz=10 (may wrap across 2 lines)
    """
    records: list[FeatRecord] = []
    seen: set[str] = set()

    for page in pages:
        page_num = page.page_number
        half = float(page.width) / 2

        for left_col in (True, False):
            x_min = 0.0 if left_col else half - 2
            x_max = half - 2 if left_col else float(page.width)
            col_chars = [c for c in page.chars if x_min <= c["x0"] < x_max]

            lines = _group_into_lines(col_chars)

            # Build a typed line sequence: ("name", text, y) | ("tag", text, y)
            typed: list[tuple[str, str, float]] = []
            for y, group in lines:
                name_chars = [c for c in group if _char_is_feat_name(c)]
                tag_chars  = [c for c in group if _char_is_feat_tag(c)]
                if name_chars:
                    text = "".join(c["text"] for c in name_chars).strip()
                    if text:
                        typed.append(("name", text, y))
                if tag_chars:
                    text = "".join(c["text"] for c in tag_chars).strip()
                    if text:
                        typed.append(("tag", text, y))

            # Pair each feat name with the immediately following tag lines.
            # Tag lines may wrap (e.g. "Fighting Style Feat (Prerequisite: Fighting
            # Style Feature)") so we concatenate consecutive tags until the next name.
            idx = 0
            while idx < len(typed):
                kind, text, _ = typed[idx]
                if kind != "name":
                    idx += 1
                    continue

                feat_name = clean_text(text)
                # Gather following tag lines
                tag_parts: list[str] = []
                j = idx + 1
                while j < len(typed) and typed[j][0] == "tag":
                    tag_parts.append(typed[j][1])
                    j += 1

                if tag_parts:
                    tag_text = clean_text(" ".join(tag_parts))
                    m = _FEAT_TYPE_RE.match(tag_text)
                    if m and feat_name not in seen:
                        seen.add(feat_name)
                        records.append(FeatRecord(
                            name=feat_name,
                            feat_type=m.group(1).strip().title(),
                            prerequisite=clean_text(m.group(2) or ""),
                            page_number=page_num,
                        ))

                idx += 1

    if len(records) < 5:
        raise ValueError(
            f"Feat parser produced only {len(records)} feats — expected ≥5."
        )
    return records


def _page_chapter_title(page) -> str:
    """Return the chapter-level heading text on a page, or '' if none."""
    heading_chars = [
        c for c in page.chars
        if _CHAPTER_FONT in c.get("fontname", "")
        and abs(c.get("size", 0) - _CHAPTER_SIZE) < 0.5
    ]
    if not heading_chars:
        return ""
    heading_chars.sort(key=lambda c: c["x0"])
    return "".join(c["text"] for c in heading_chars).strip()


def extract_feats_from_pdf(pdf_path: str) -> list[FeatRecord]:
    """Extract feat records from the SRD PDF.

    Scans from the 'Feats' chapter heading through to the 'Equipment' heading.
    Raises ValueError if fewer than 10 feats found.
    """
    feat_pages: list = []

    with pdfplumber.open(pdf_path) as pdf:
        in_feats = False
        for page in pdf.pages:
            title = _page_chapter_title(page)
            if not in_feats:
                if title == "Feats":
                    in_feats = True
            if not in_feats:
                continue
            if title == "Equipment":
                break
            feat_pages.append(page)

    records = extract_feats(feat_pages)
    if len(records) < 10:
        raise ValueError(
            f"Feat parser produced only {len(records)} feats — expected ≥10."
        )
    return records


# ---------------------------------------------------------------------------
# Species
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SpeciesRecord:
    """A single species extracted from the SRD PDF."""

    name: str
    speed_text: str  # e.g. "30 feet" or "35 feet"
    page_number: int = 0


# Real PDF font profile (verified against SRD CC v5.2, pages 83-86):
#   sz=12 GillSans-SemiBold  → species name  (e.g. "Dragonborn")
#   sz=10 GillSans-SemiBold  → trait label   (e.g. "Speed:")
#   sz=10 GillSans           → trait value   (e.g. " 30 feet") — same row as label
#   sz=14 GillSans-SemiBold  → section header (e.g. "Species Descriptions") — skip
#   sz=18 GillSans-SemiBold  → sub-chapter   (e.g. "Character Species") — skip
#   sz=26 GillSans-SemiBold  → chapter heading (e.g. "Character Origins") — for page detection
_SPECIES_NAME_FONT = "GillSans-SemiBold"
_SPECIES_NAME_SIZE = 12.0

_SPEED_LABEL_FONT = "GillSans-SemiBold"
_SPEED_LABEL_SIZE = 10.0

_SPEED_VALUE_FONT = "GillSans"
_SPEED_VALUE_SIZE = 10.0

_SPEED_VALUE_RE = re.compile(r"(\d+\s*feet)")


def _col_speed_labels(col_chars: list[dict]) -> dict[int, tuple[float, str]]:
    """Return {rounded_y: (raw_top, speed_value)} for all 'Speed:' labels in a column.

    The Speed: label is GillSans-SemiBold sz=10; the value is GillSans sz=10
    on the same row (within 2 pts).
    """
    # Group label chars by rounded y
    label_rows: dict[int, list[dict]] = {}
    for c in col_chars:
        if (
            _SPEED_LABEL_FONT in c.get("fontname", "")
            and abs(c.get("size", 0) - _SPEED_LABEL_SIZE) < 0.5
        ):
            y = round(c["top"])
            label_rows.setdefault(y, []).append(c)

    result: dict[int, tuple[float, str]] = {}
    for y, lchars in label_rows.items():
        row_text = "".join(c["text"] for c in sorted(lchars, key=lambda c: c["x0"]))
        if "Speed" not in row_text:
            continue
        raw_top = lchars[0]["top"]
        # Value chars: GillSans (non-SemiBold) sz=10, same y ±2 pts, same column
        val_chars = [
            c for c in col_chars
            if _SPEED_VALUE_FONT in c.get("fontname", "")
            and _SPEED_LABEL_FONT not in c.get("fontname", "")
            and abs(c.get("size", 0) - _SPEED_VALUE_SIZE) < 0.5
            and abs(c["top"] - raw_top) < 2.0
        ]
        val_text = "".join(
            c["text"] for c in sorted(val_chars, key=lambda c: c["x0"])
        ).strip()
        m = _SPEED_VALUE_RE.search(val_text)
        if m:
            result[y] = (raw_top, m.group(1).strip())
    return result


_SPECIES_SECTION_SIZE = 14.0  # sz=14 GillSans-SemiBold marks section headers


def _col_species_descriptions_y(col_chars: list[dict]) -> float | None:
    """Return the y of the 'Species Descriptions' sz=14 header in this column, or None."""
    sec_rows: dict[int, list[dict]] = {}
    for c in col_chars:
        if (
            _SPECIES_NAME_FONT in c.get("fontname", "")
            and abs(c.get("size", 0) - _SPECIES_SECTION_SIZE) < 0.5
        ):
            y = round(c["top"])
            sec_rows.setdefault(y, []).append(c)

    for y in sorted(sec_rows):
        text = "".join(c["text"] for c in sorted(sec_rows[y], key=lambda c: c["x0"]))
        if "Descriptions" in text:
            return float(y)
    return None


def extract_species(pages: list) -> list[SpeciesRecord]:
    """Extract SpeciesRecords from a list of pdfplumber page objects.

    Font-aware extraction verified against SRD CC v5.2:
      - Species names: GillSans-SemiBold sz=12
      - Speed label:   GillSans-SemiBold sz=10  (e.g. "Speed:")
      - Speed value:   GillSans sz=10           (e.g. " 30 feet"), same row as label

    Within each column, only sz=12 entries that:
      (a) appear at or after a 'Species Descriptions' sz=14 header (if one exists
          in that column), AND
      (b) have a Speed: label below them in that column
    are accepted.  This filters out "Speed" / "Special Traits" sub-topic headings
    from the introductory 'Parts of a Species' section on page 84.
    """
    records: list[SpeciesRecord] = []
    seen: set[str] = set()

    for page in pages:
        page_num = page.page_number
        half = float(page.width) / 2

        for left_col in (True, False):
            x_min = 0.0 if left_col else half - 2
            x_max = half - 2 if left_col else float(page.width)
            col_chars = [c for c in page.chars if x_min <= c["x0"] < x_max]

            # If this column has a 'Species Descriptions' section header, only
            # accept species names that appear after it.
            descriptions_y = _col_species_descriptions_y(col_chars)
            min_name_y = descriptions_y if descriptions_y is not None else 0.0

            # Collect Speed: positions and values for this column
            speed_map = _col_speed_labels(col_chars)
            sorted_speed_ys = sorted(speed_map)

            # Find species name candidates: sz=12 GillSans-SemiBold
            name_rows: dict[int, list[dict]] = {}
            for c in col_chars:
                if (
                    _SPECIES_NAME_FONT in c.get("fontname", "")
                    and abs(c.get("size", 0) - _SPECIES_NAME_SIZE) < 0.5
                ):
                    y = round(c["top"])
                    name_rows.setdefault(y, []).append(c)

            for name_y in sorted(name_rows):
                # Skip entries in the introductory section (before Descriptions header)
                if name_y < min_name_y:
                    continue

                name_text = clean_text(
                    "".join(
                        c["text"] for c in sorted(name_rows[name_y], key=lambda c: c["x0"])
                    )
                )
                if not name_text or name_text in seen:
                    continue

                # Find the first Speed: label below this name in the same column
                next_speed_ys = [sy for sy in sorted_speed_ys if sy > name_y]
                if not next_speed_ys:
                    # No speed follows → not a species entry (e.g. background sub-topic)
                    continue

                speed_value = speed_map[next_speed_ys[0]][1]
                seen.add(name_text)
                records.append(SpeciesRecord(
                    name=name_text,
                    speed_text=speed_value,
                    page_number=page_num,
                ))

    if len(records) < 3:
        raise ValueError(
            f"Species parser produced only {len(records)} species — expected ≥3."
        )
    return records


def extract_species_from_pdf(pdf_path: str) -> list[SpeciesRecord]:
    """Extract species records from the SRD PDF.

    Scans from the 'Character Origins' chapter heading through to the 'Feats'
    chapter heading (using the same sz=26 GillSans-SemiBold detection as
    extract_feats_from_pdf).

    Raises ValueError if fewer than 5 species found.
    """
    species_pages: list = []

    with pdfplumber.open(pdf_path) as pdf:
        in_origins = False
        for page in pdf.pages:
            title = _page_chapter_title(page)
            if not in_origins:
                if title == "Character Origins":
                    in_origins = True
            if not in_origins:
                continue
            if title == "Feats":
                break
            species_pages.append(page)

    records = extract_species(species_pages)
    if len(records) < 5:
        raise ValueError(
            f"Species parser produced only {len(records)} species — expected ≥5."
        )
    return records
