"""Extract character class records from SRD PDF text."""
from __future__ import annotations
import re
from dataclasses import dataclass
import pdfplumber

from .base import clean_text


@dataclass(frozen=True)
class ClassRecord:
    name: str
    hit_dice: str   # lowercase: "d6", "d8", "d10", "d12"
    page_number: int = 0


# Matches "Hit Point Die D12 per Barbarian level"
_HIT_DIE_RE = re.compile(
    r"Hit\s+Point\s+Die\s+(D\d+)\s+per\s+(\w+)\s+level",
    re.IGNORECASE,
)


def extract_classes(text: str) -> list[ClassRecord]:
    """Parse ClassRecords from plain extracted text.

    Uses the 'Hit Point Die D{n} per {Name} level' pattern which appears
    once per base class in the classes chapter of the SRD.
    """
    records = []
    seen: set[str] = set()
    for m in _HIT_DIE_RE.finditer(text):
        hit_dice = m.group(1).lower()   # "D12" → "d12"
        name = m.group(2).strip().title()
        if name not in seen:
            seen.add(name)
            records.append(ClassRecord(name=name, hit_dice=hit_dice))
    if not records:
        raise ValueError("found no classes in the provided text")
    return records


def extract_classes_from_pdf(pdf_path: str) -> list[ClassRecord]:
    """Extract class records from the SRD PDF.

    Scans all pages for 'Hit Point Die D{n} per {Name} level' patterns.
    Raises ValueError if fewer than 10 classes found.
    """
    records_by_name: dict[str, ClassRecord] = {}

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = clean_text(page.extract_text() or "")
            for m in _HIT_DIE_RE.finditer(text):
                hit_dice = m.group(1).lower()
                name = m.group(2).strip().title()
                if name not in records_by_name:
                    records_by_name[name] = ClassRecord(
                        name=name,
                        hit_dice=hit_dice,
                        page_number=page.page_number,
                    )

    records = list(records_by_name.values())
    if len(records) < 10:
        raise ValueError(
            f"Class parser produced only {len(records)} classes — expected ≥10. "
            "Check PDF path and text extraction."
        )
    return records
