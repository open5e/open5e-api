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
            # Tag lines may wrap (e.g. "Fighting Style Feat (Prerequisite: Fighting Style\nFeature)")
            # so we concatenate consecutive tag entries until hitting another name or end.
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
