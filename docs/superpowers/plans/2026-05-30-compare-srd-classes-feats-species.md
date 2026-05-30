# SRD Compare: Classes, Feats, Species Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add CharacterClass, Feat, and Species entity types to the `compare_srd` management command, each with PDF parsers and comparison logic.

**Architecture:** Three new parsers follow the existing pattern in `data/raw_sources/srd_5_2/parsers/`. Classes uses plain-text regex (the "Hit Point Die D12 per Barbarian level" string is uniquely parseable without font awareness). Feats and Species use font-aware extraction (both have entity names at GillSans-SemiBold size 14 in their respective sections). All three add runners and field maps to `compare_srd.py` following the existing pattern exactly.

**Description fields:** DB `desc` is empty for CharacterClass and very short for Feat/Species. Description comparison would only produce noise, so `desc` is added to `SKIP_FIELDS` for all three new types (same as existing entities). The infrastructure is there if descriptions are populated later.

**Tech Stack:** pdfplumber (font-aware character extraction), Django ORM, pytest, existing `data/raw_sources/srd_5_2/parsers/base.py` utilities.

---

## Key facts gathered from codebase

**PDF section locations:**
- Classes chapter: pages 28–82 (each class has "Hit Point Die D{n} per {Name} level")
- Species section: pages 83–86 (within "Character Origins" chapter)
- Feats section: pages 87–88

**Font taxonomy for new sections (GillSans-SemiBold):**
- sz=18: base class names ("Barbarian", "Bard", ...)
- sz=14: feat names and species names
- sz=12: feat category tags ("Origin Feat", "General Feat (Prerequisite: Level 4+)", ...)

**DB field values (as stored):**
- `CharacterClass.hit_dice`: `'D6'`, `'D8'`, `'D10'`, `'D12'`
- `Feat.type`: `'Origin'`, `'General'`, `'Fighting Style'`, `'Epic Boon'`
- `Feat.prerequisite`: `''`, `'Level 4+'`, `'Fighting Style Feature'`, `'Level 19+'`, etc.
- `SpeciesTrait` with `type='SPEED'` has `desc` = `'30 feet'` (text, not int)

**DB queries:**
```python
# Classes (base classes only, no subclasses)
CharacterClass.objects.filter(document_id=doc, subclass_of=None).values('name', 'hit_dice')

# Feats
Feat.objects.filter(document_id=doc).values('name', 'type', 'prerequisite')

# Species (base species only, no subspecies)
Species.objects.filter(document_id=doc, subspecies_of=None).values('name')

# Species speed (from trait — joined in the runner)
SpeciesTrait.objects.filter(type='SPEED', parent__document_id=doc, parent__subspecies_of=None)\
    .values('parent__name', 'desc')
# → {species_name: speed_text} e.g. {"Dragonborn": "30 feet"}
```

---

## File structure

| File | Action | Responsibility |
|------|--------|----------------|
| `data/raw_sources/srd_5_2/parsers/classes.py` | Create | `ClassRecord` dataclass + `extract_classes_from_pdf()` |
| `data/raw_sources/srd_5_2/parsers/origins.py` | Create | `FeatRecord`, `SpeciesRecord` + `extract_feats_from_pdf()`, `extract_species_from_pdf()` |
| `api_v2/management/commands/compare_srd.py` | Modify | Add field maps, runners, skip fields for all three |
| `api_v2/tests/test_srd_parsers.py` | Modify | Parser unit tests using mock PDF pages |
| `api_v2/tests/test_compare_srd.py` | Modify | Comparison logic tests |

---

## Task 1: ClassRecord parser

**Files:**
- Create: `data/raw_sources/srd_5_2/parsers/classes.py`
- Test: `api_v2/tests/test_srd_parsers.py`

Uses plain-text regex. The string "Hit Point Die D12 per Barbarian level" uniquely identifies both class name and hit die in the same line — no font-aware extraction needed.

- [ ] **Step 1: Write the failing tests**

Add to `api_v2/tests/test_srd_parsers.py`:

```python
from data.raw_sources.srd_5_2.parsers.classes import ClassRecord, extract_classes


class TestExtractClasses:
    def test_extracts_hit_dice(self):
        text = """
Barbarian
Core Barbarian Traits
Primary Ability Strength
Hit Point Die D12 per Barbarian level
Saving Throw Strength and Constitution
"""
        records = extract_classes(text)
        assert any(r.name == "Barbarian" and r.hit_dice == "d12" for r in records)

    def test_extracts_multiple_classes(self):
        text = """
Hit Point Die D12 per Barbarian level
Hit Point Die D8 per Bard level
Hit Point Die D6 per Wizard level
"""
        records = extract_classes(text)
        assert len(records) == 3
        by_name = {r.name: r for r in records}
        assert by_name["Barbarian"].hit_dice == "d12"
        assert by_name["Bard"].hit_dice == "d8"
        assert by_name["Wizard"].hit_dice == "d6"

    def test_hit_dice_lowercased(self):
        """hit_dice is always lowercase for comparison with DB values."""
        records = extract_classes("Hit Point Die D10 per Fighter level")
        assert records[0].hit_dice == "d10"

    def test_sanity_check_raises_on_empty(self):
        import pytest
        with pytest.raises(ValueError, match="found no classes"):
            extract_classes("")

    def test_single_word_class_name_captured(self):
        """Regex captures the single class name word correctly."""
        records = extract_classes("Hit Point Die D8 per Rogue level")
        assert any(r.name == "Rogue" for r in records)


class TestExtractClassesFromPdf:
    def test_raises_when_no_classes_found(self, tmp_path):
        import pdfplumber, pytest
        from unittest.mock import patch, MagicMock
        from data.raw_sources.srd_5_2.parsers.classes import extract_classes_from_pdf
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "No classes here"
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = lambda s: s
        mock_pdf.__exit__ = MagicMock(return_value=False)
        with patch("pdfplumber.open", return_value=mock_pdf):
            with pytest.raises(ValueError, match="expected ≥10"):
                extract_classes_from_pdf("fake.pdf")
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
.venv/bin/python -m pytest api_v2/tests/test_srd_parsers.py::TestExtractClasses -v
```
Expected: ImportError (module doesn't exist yet)

- [ ] **Step 3: Implement `data/raw_sources/srd_5_2/parsers/classes.py`**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
.venv/bin/python -m pytest api_v2/tests/test_srd_parsers.py::TestExtractClasses api_v2/tests/test_srd_parsers.py::TestExtractClassesFromPdf -v
```
Expected: all PASS

- [ ] **Step 5: Verify against real PDF**

```bash
.venv/bin/python -c "
from data.raw_sources.srd_5_2.parsers.classes import extract_classes_from_pdf
records = extract_classes_from_pdf('data/raw_sources/srd_5_2/SRD_CC_v5.2.pdf')
for r in sorted(records, key=lambda x: x.name):
    print(f'{r.name}: {r.hit_dice} (p{r.page_number})')
print(f'Total: {len(records)}')
"
```
Expected: 12 classes with correct hit dice (d6→Sorcerer/Wizard, d8→Bard/Cleric/Druid/Monk/Rogue/Warlock, d10→Fighter/Paladin/Ranger, d12→Barbarian)

- [ ] **Step 6: Commit**

```bash
git add data/raw_sources/srd_5_2/parsers/classes.py api_v2/tests/test_srd_parsers.py
git commit -m "feat: add CharacterClass PDF parser (hit_dice extraction)"
```

---

## Task 2: Feat parser

**Files:**
- Create: `data/raw_sources/srd_5_2/parsers/origins.py`
- Test: `api_v2/tests/test_srd_parsers.py`

Font-aware extraction: feat names appear at GillSans-SemiBold size 14, and the category tag ("Origin Feat", "General Feat (Prerequisite: …)") appears at size 12 in the same column immediately after the name.

- [ ] **Step 1: Write the failing tests**

Add to `api_v2/tests/test_srd_parsers.py`:

```python
from data.raw_sources.srd_5_2.parsers.origins import FeatRecord, extract_feats


class TestExtractFeats:
    def _make_page(self, lines):
        """Build mock pdfplumber page chars from (text, font, size, x, y) tuples."""
        from unittest.mock import MagicMock
        chars = []
        for text, font, size, x, y in lines:
            for i, ch in enumerate(text):
                chars.append({
                    "text": ch, "fontname": f"XXXX+{font}",
                    "size": size, "x0": x + i * 6, "top": y,
                })
        page = MagicMock()
        page.page_number = 1
        page.width = 600.0
        page.chars = chars
        return page

    def _feat_chars(self, name, category, prerequisite=None, x=50, y_name=100):
        """Helper to build chars for a feat entry."""
        cat_text = category
        if prerequisite:
            cat_text += f" (Prerequisite: {prerequisite})"
        return (
            [(name, "GillSans-SemiBold", 14, x, y_name)]
            + [(cat_text, "GillSans-SemiBold", 12, x, y_name + 14)]
        )

    def test_extracts_origin_feat(self):
        chars = self._feat_chars("Alert", "Origin Feat")
        page = self._make_page(chars)
        records = extract_feats([page])
        assert len(records) == 1
        r = records[0]
        assert r.name == "Alert"
        assert r.feat_type == "Origin"
        assert r.prerequisite == ""

    def test_extracts_general_feat_with_prerequisite(self):
        chars = self._feat_chars(
            "Ability Score Improvement", "General Feat", "Level 4+"
        )
        page = self._make_page(chars)
        records = extract_feats([page])
        assert records[0].feat_type == "General"
        assert records[0].prerequisite == "Level 4+"

    def test_extracts_fighting_style_feat(self):
        chars = self._feat_chars(
            "Archery", "Fighting Style Feat", "Fighting Style Feature"
        )
        page = self._make_page(chars)
        records = extract_feats([page])
        assert records[0].feat_type == "Fighting Style"

    def test_extracts_epic_boon_feat(self):
        chars = self._feat_chars(
            "Boon of Combat Prowess", "Epic Boon Feat", "Level 19+"
        )
        page = self._make_page(chars)
        records = extract_feats([page])
        assert records[0].feat_type == "Epic Boon"

    def test_ignores_non_feat_sz14_text(self):
        """Section headers like 'Parts of a Feat' at sz=14 are not feats."""
        chars = [("Parts of a Feat", "GillSans-SemiBold", 14, 50, 100)]
        # No sz=12 "[Type] Feat" line follows → not a feat
        page = self._make_page(chars)
        records = extract_feats([page])
        assert records == []

    def test_sanity_check_raises_on_empty(self):
        import pytest
        from unittest.mock import MagicMock
        page = MagicMock()
        page.page_number = 1
        page.width = 600.0
        page.chars = []
        with pytest.raises(ValueError, match="expected ≥5"):
            extract_feats([page])
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
.venv/bin/python -m pytest api_v2/tests/test_srd_parsers.py::TestExtractFeats -v
```
Expected: ImportError

- [ ] **Step 3: Implement feat parser in `data/raw_sources/srd_5_2/parsers/origins.py`**

```python
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
    name: str
    feat_type: str      # "Origin", "General", "Fighting Style", "Epic Boon"
    prerequisite: str   # empty string when none
    page_number: int = 0


_FEAT_NAME_FONT = "GillSans-SemiBold"
_FEAT_NAME_SIZE = 14.0    # feat names
_FEAT_TAG_SIZE = 12.0     # "Origin Feat (Prerequisite: ...)" tag

_FEAT_TYPE_RE = re.compile(
    r"^(Origin|General|Fighting Style|Epic Boon)\s+Feat"
    r"(?:\s*\(Prerequisite:\s*([^)]+)\))?",
    re.IGNORECASE,
)


def _is_feat_name_char(char: dict) -> bool:
    font = char.get("fontname", "")
    size = char.get("size", 0)
    return _FEAT_NAME_FONT in font and abs(size - _FEAT_NAME_SIZE) < 0.5


def _is_feat_tag_char(char: dict) -> bool:
    font = char.get("fontname", "")
    size = char.get("size", 0)
    return _FEAT_NAME_FONT in font and abs(size - _FEAT_TAG_SIZE) < 0.5


def extract_feats(pages: list) -> list[FeatRecord]:
    """Extract FeatRecords from a list of pdfplumber page objects.

    Uses font-aware extraction: feat names are GillSans-SemiBold size 14,
    immediately followed by a size-12 category tag in the same column.
    """
    records: list[FeatRecord] = []
    seen: set[str] = set()

    for page in pages:
        page_num = page.page_number
        half = float(page.width) / 2

        for left_col in (True, False):
            if left_col:
                col_chars = [c for c in page.chars if c["x0"] < half - 2]
            else:
                col_chars = [c for c in page.chars if c["x0"] >= half - 2]

            # Group chars into lines by y-proximity
            col_chars.sort(key=lambda c: (c["top"], c["x0"]))
            lines: list[tuple[float, str, str]] = []  # (y, text, kind)
            i = 0
            while i < len(col_chars):
                y0 = col_chars[i]["top"]
                line_chars = []
                while i < len(col_chars) and abs(col_chars[i]["top"] - y0) <= 4:
                    line_chars.append(col_chars[i])
                    i += 1
                name_chars = [c for c in line_chars if _is_feat_name_char(c)]
                tag_chars = [c for c in line_chars if _is_feat_tag_char(c)]
                if name_chars:
                    name_chars.sort(key=lambda c: c["x0"])
                    text = "".join(c["text"] for c in name_chars).strip()
                    if text:
                        lines.append((y0, text, "name"))
                if tag_chars:
                    tag_chars.sort(key=lambda c: c["x0"])
                    text = "".join(c["text"] for c in tag_chars).strip()
                    if text:
                        lines.append((y0 + 0.001, text, "tag"))

            # Pair each name with the immediately following tag
            for idx, (y, text, kind) in enumerate(lines):
                if kind != "name":
                    continue
                # Look for the next line that is a tag
                for _, tag_text, tag_kind in lines[idx + 1:]:
                    if tag_kind == "tag":
                        m = _FEAT_TYPE_RE.match(clean_text(tag_text))
                        if m:
                            feat_name = clean_text(text)
                            if feat_name not in seen:
                                seen.add(feat_name)
                                records.append(FeatRecord(
                                    name=feat_name,
                                    feat_type=m.group(1).strip().title()
                                        .replace("Style", "Style"),
                                    prerequisite=clean_text(m.group(2) or ""),
                                    page_number=page_num,
                                ))
                        break  # only check first following tag line
                    elif tag_kind == "name":
                        break  # hit the next feat name — no tag for this one

    if len(records) < 5:
        raise ValueError(
            f"Feat parser produced only {len(records)} feats — expected ≥5."
        )
    return records


def extract_feats_from_pdf(pdf_path: str) -> list[FeatRecord]:
    """Extract feat records from the SRD PDF.

    Scans from the 'Feats' section through to the 'Equipment' section.
    Raises ValueError if fewer than 10 feats found.
    """
    feat_pages: list = []

    with pdfplumber.open(pdf_path) as pdf:
        in_feats = False
        for page in pdf.pages:
            text = page.extract_text() or ""
            if not in_feats:
                if re.search(r"^Feats\s*$", text, re.MULTILINE):
                    in_feats = True
            if not in_feats:
                continue
            if re.search(r"^Equipment\s*$", text, re.MULTILINE) and in_feats:
                break
            feat_pages.append(page)

    records = extract_feats(feat_pages)
    if len(records) < 10:
        raise ValueError(
            f"Feat parser produced only {len(records)} feats — expected ≥10."
        )
    return records
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
.venv/bin/python -m pytest api_v2/tests/test_srd_parsers.py::TestExtractFeats -v
```
Expected: all PASS

- [ ] **Step 5: Verify against real PDF**

```bash
.venv/bin/python -c "
from data.raw_sources.srd_5_2.parsers.origins import extract_feats_from_pdf
records = extract_feats_from_pdf('data/raw_sources/srd_5_2/SRD_CC_v5.2.pdf')
for r in sorted(records, key=lambda x: x.name):
    print(f'{r.name!r}: type={r.feat_type!r} prereq={r.prerequisite!r} p{r.page_number}')
print(f'Total: {len(records)}')
"
```
Expected: ~17 feats matching the DB (Alert, Magic Initiate, Savage Attacker, Skilled, Ability Score Improvement, Grappler, Archery, Defense, Great Weapon Fighting, Two-Weapon Fighting, 7× Boon of …)

- [ ] **Step 6: Commit**

```bash
git add data/raw_sources/srd_5_2/parsers/origins.py api_v2/tests/test_srd_parsers.py
git commit -m "feat: add Feat PDF parser (type + prerequisite extraction)"
```

---

## Task 3: Species parser

**Files:**
- Modify: `data/raw_sources/srd_5_2/parsers/origins.py`
- Test: `api_v2/tests/test_srd_parsers.py`

Font-aware: species names appear at GillSans-SemiBold size 14 in the species section. Speed is extracted from the "Speed: N feet" pattern in the plain text near each name.

- [ ] **Step 1: Write the failing tests**

Add to `api_v2/tests/test_srd_parsers.py`:

```python
from data.raw_sources.srd_5_2.parsers.origins import SpeciesRecord, extract_species


class TestExtractSpecies:
    def _make_page(self, lines, page_number=1):
        from unittest.mock import MagicMock
        chars = []
        for text, font, size, x, y in lines:
            for i, ch in enumerate(text):
                chars.append({
                    "text": ch, "fontname": f"XXXX+{font}",
                    "size": size, "x0": x + i * 6, "top": y,
                })
        page = MagicMock()
        page.page_number = page_number
        page.width = 600.0
        page.chars = chars
        page.extract_text.return_value = "\n".join(
            t for t, _, _, _, _ in lines
        )
        return page

    def test_extracts_species_name_and_speed(self):
        from unittest.mock import MagicMock
        page = MagicMock()
        page.page_number = 1
        page.width = 600.0
        page.chars = []
        # Species names at sz=14, speed extracted from page text
        page.extract_text.return_value = (
            "Dragonborn\nCreature Type: Humanoid\nSize: Medium or Small\nSpeed: 30 feet\n"
        )
        # Add sz=14 char for the name
        page.chars = [
            {"text": c, "fontname": "XXXX+GillSans-SemiBold", "size": 14.0,
             "x0": i * 6, "top": 50}
            for i, c in enumerate("Dragonborn")
        ]
        records = extract_species([page])
        assert len(records) == 1
        assert records[0].name == "Dragonborn"
        assert records[0].speed_text == "30 feet"

    def test_extracts_multiple_species(self):
        from unittest.mock import MagicMock
        page = MagicMock()
        page.page_number = 1
        page.width = 600.0
        # Two species on same page
        page.extract_text.return_value = (
            "Dragonborn\nSpeed: 30 feet\n"
            "Dwarf\nSpeed: 30 feet\n"
        )
        page.chars = (
            [{"text": c, "fontname": "XXXX+GillSans-SemiBold", "size": 14.0,
              "x0": i * 6, "top": 50} for i, c in enumerate("Dragonborn")]
            + [{"text": c, "fontname": "XXXX+GillSans-SemiBold", "size": 14.0,
                "x0": i * 6, "top": 200} for i, c in enumerate("Dwarf")]
        )
        records = extract_species([page])
        assert {r.name for r in records} == {"Dragonborn", "Dwarf"}

    def test_sanity_check_raises_on_empty(self):
        import pytest
        from unittest.mock import MagicMock
        page = MagicMock()
        page.page_number = 1
        page.width = 600.0
        page.chars = []
        page.extract_text.return_value = ""
        with pytest.raises(ValueError, match="expected ≥3"):
            extract_species([page])
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
.venv/bin/python -m pytest api_v2/tests/test_srd_parsers.py::TestExtractSpecies -v
```
Expected: ImportError (SpeciesRecord not yet defined)

- [ ] **Step 3: Add SpeciesRecord and `extract_species` to `origins.py`**

Add below the feat section in `data/raw_sources/srd_5_2/parsers/origins.py`:

```python
# ---------------------------------------------------------------------------
# Species
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SpeciesRecord:
    name: str
    speed_text: str    # "30 feet", "35 feet", etc. — matches SpeciesTrait.desc
    page_number: int = 0


_SPECIES_NAME_SIZE = 14.0  # same size as feat names; section context distinguishes them
_SPEED_RE = re.compile(r"Speed:\s*(\d+\s*feet)", re.IGNORECASE)


def _extract_sz14_names_from_page(page) -> list[tuple[str, int]]:
    """Return list of (name, page_number) for GillSans-SemiBold size-14 text on this page."""
    half = float(page.width) / 2
    results = []
    for left_col in (True, False):
        if left_col:
            col_chars = [c for c in page.chars if c["x0"] < half - 2]
        else:
            col_chars = [c for c in page.chars if c["x0"] >= half - 2]
        col_chars = [
            c for c in col_chars
            if _FEAT_NAME_FONT in c.get("fontname", "")
            and abs(c.get("size", 0) - _SPECIES_NAME_SIZE) < 0.5
        ]
        col_chars.sort(key=lambda c: (c["top"], c["x0"]))
        i = 0
        while i < len(col_chars):
            y0 = col_chars[i]["top"]
            line_chars = []
            while i < len(col_chars) and abs(col_chars[i]["top"] - y0) <= 4:
                line_chars.append(col_chars[i])
                i += 1
            line_chars.sort(key=lambda c: c["x0"])
            text = "".join(c["text"] for c in line_chars).strip()
            if text:
                results.append((text, page.page_number))
    return results


def extract_species(pages: list) -> list[SpeciesRecord]:
    """Extract SpeciesRecords from a list of pdfplumber page objects.

    Finds species names (GillSans-SemiBold size 14) then searches the page
    plain text for the 'Speed: N feet' value associated with each name.
    The plain text of the full page is used for speed lookup since the
    speed line is always on the same page as the species name.
    """
    records: list[SpeciesRecord] = []
    seen: set[str] = set()

    for page in pages:
        page_text = clean_text(page.extract_text() or "")
        names = _extract_sz14_names_from_page(page)

        for name, page_num in names:
            name = clean_text(name)
            if name in seen:
                continue
            # Find 'Speed: N feet' near this name in the page text.
            # Locate the name in the page text, then search forward.
            name_pos = page_text.lower().find(name.lower())
            if name_pos == -1:
                continue
            after = page_text[name_pos:]
            m = _SPEED_RE.search(after)
            if not m:
                continue
            # Ensure the speed is before the next species name
            speed_text = clean_text(m.group(1))
            seen.add(name)
            records.append(SpeciesRecord(
                name=name,
                speed_text=speed_text,
                page_number=page_num,
            ))

    if len(records) < 3:
        raise ValueError(
            f"Species parser produced only {len(records)} species — expected ≥3."
        )
    return records


def extract_species_from_pdf(pdf_path: str) -> list[SpeciesRecord]:
    """Extract species records from the SRD PDF Character Origins chapter.

    Scans from the 'Character Origins' section through to 'Feats'.
    Raises ValueError if fewer than 5 species found.
    """
    species_pages: list = []

    with pdfplumber.open(pdf_path) as pdf:
        in_origins = False
        for page in pdf.pages:
            text = page.extract_text() or ""
            if not in_origins:
                if re.search(r"Character\s+Origins", text, re.IGNORECASE):
                    in_origins = True
            if not in_origins:
                continue
            if re.search(r"^Feats\s*$", text, re.MULTILINE) and in_origins:
                break
            species_pages.append(page)

    records = extract_species(species_pages)
    if len(records) < 5:
        raise ValueError(
            f"Species parser produced only {len(records)} species — expected ≥5."
        )
    return records
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
.venv/bin/python -m pytest api_v2/tests/test_srd_parsers.py::TestExtractSpecies -v
```
Expected: all PASS

- [ ] **Step 5: Verify against real PDF**

```bash
.venv/bin/python -c "
from data.raw_sources.srd_5_2.parsers.origins import extract_species_from_pdf
records = extract_species_from_pdf('data/raw_sources/srd_5_2/SRD_CC_v5.2.pdf')
for r in sorted(records, key=lambda x: x.name):
    print(f'{r.name}: speed={r.speed_text!r} (p{r.page_number})')
print(f'Total: {len(records)}')
"
```
Expected: 9 species (Dragonborn, Dwarf, Elf, Gnome, Goliath, Halfling, Human, Orc, Tiefling). Goliath has "35 feet" speed; all others have "30 feet"

- [ ] **Step 6: Commit**

```bash
git add data/raw_sources/srd_5_2/parsers/origins.py api_v2/tests/test_srd_parsers.py
git commit -m "feat: add Species PDF parser (name + speed extraction)"
```

---

## Task 4: compare_srd.py additions

**Files:**
- Modify: `api_v2/management/commands/compare_srd.py`
- Test: `api_v2/tests/test_compare_srd.py`

Wire up the three new parsers into the compare_srd management command. Follows the exact same pattern as existing runners.

- [ ] **Step 1: Write failing comparison tests**

Add to `api_v2/tests/test_compare_srd.py`:

```python
from data.raw_sources.srd_5_2.parsers.classes import ClassRecord
from data.raw_sources.srd_5_2.parsers.origins import FeatRecord, SpeciesRecord


def _make_class(name, hit_dice="d8"):
    return ClassRecord(name=name, hit_dice=hit_dice)

def _make_feat(name, feat_type="Origin", prerequisite=""):
    return FeatRecord(name=name, feat_type=feat_type, prerequisite=prerequisite)

def _make_species(name, speed_text="30 feet"):
    return SpeciesRecord(name=name, speed_text=speed_text)


class TestCompareClasses:
    SKIP = {"desc"}

    def test_hit_dice_case_insensitive(self):
        """PDF 'd12' matches DB 'D12'."""
        pdf = [_make_class("Barbarian", hit_dice="d12")]
        db = [{"name": "Barbarian", "hit_dice": "D12"}]
        result = compare_records("classes", pdf, db, skip_fields=self.SKIP)
        assert result.mismatches == []

    def test_hit_dice_mismatch_detected(self):
        pdf = [_make_class("Barbarian", hit_dice="d8")]
        db = [{"name": "Barbarian", "hit_dice": "D12"}]
        result = compare_records("classes", pdf, db, skip_fields=self.SKIP)
        assert any(m.field == "hit_dice" for m in result.mismatches)

    def test_missing_class_detected(self):
        pdf = [_make_class("Barbarian"), _make_class("Wizard")]
        db = [{"name": "Barbarian", "hit_dice": "D12"}]
        result = compare_records("classes", pdf, db, skip_fields=self.SKIP)
        assert "Wizard" in result.missing

    def test_extra_class_detected(self):
        pdf = [_make_class("Barbarian")]
        db = [{"name": "Barbarian", "hit_dice": "D12"}, {"name": "Mystic", "hit_dice": "D8"}]
        result = compare_records("classes", pdf, db, skip_fields=self.SKIP)
        assert "Mystic" in result.extra


class TestCompareFeats:
    SKIP = {"desc"}

    def test_type_match(self):
        pdf = [_make_feat("Alert", feat_type="Origin")]
        db = [{"name": "Alert", "type": "Origin", "prerequisite": ""}]
        result = compare_records("feats", pdf, db, skip_fields=self.SKIP)
        assert result.mismatches == []

    def test_type_mismatch_detected(self):
        pdf = [_make_feat("Alert", feat_type="General")]
        db = [{"name": "Alert", "type": "Origin", "prerequisite": ""}]
        result = compare_records("feats", pdf, db, skip_fields=self.SKIP)
        assert any(m.field == "feat_type" for m in result.mismatches)

    def test_prerequisite_match(self):
        # Ability Score Improvement genuinely has "Level 4+" as its only prerequisite
        pdf = [_make_feat("Ability Score Improvement", feat_type="General", prerequisite="Level 4+")]
        db = [{"name": "Ability Score Improvement", "type": "General", "prerequisite": "Level 4+"}]
        result = compare_records("feats", pdf, db, skip_fields=self.SKIP)
        assert result.mismatches == []

    def test_prerequisite_mismatch_detected(self):
        pdf = [_make_feat("Ability Score Improvement", prerequisite="Level 4+")]
        db = [{"name": "Ability Score Improvement", "type": "General", "prerequisite": "Level 8+"}]
        result = compare_records("feats", pdf, db, skip_fields=self.SKIP)
        assert any(m.field == "prerequisite" for m in result.mismatches)


class TestCompareSpecies:
    SKIP = {"desc"}

    def test_speed_text_match(self):
        pdf = [_make_species("Dragonborn", speed_text="30 feet")]
        db = [{"name": "Dragonborn", "speed_text": "30 feet"}]
        result = compare_records("species", pdf, db, skip_fields=self.SKIP)
        assert result.mismatches == []

    def test_speed_mismatch_detected(self):
        pdf = [_make_species("Elf", speed_text="35 feet")]
        db = [{"name": "Elf", "speed_text": "30 feet"}]
        result = compare_records("species", pdf, db, skip_fields=self.SKIP)
        assert any(m.field == "speed_text" for m in result.mismatches)

    def test_missing_species_detected(self):
        pdf = [_make_species("Dragonborn"), _make_species("Elf")]
        db = [{"name": "Dragonborn", "speed_text": "30 feet"}]
        result = compare_records("species", pdf, db, skip_fields=self.SKIP)
        assert "Elf" in result.missing
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
.venv/bin/python -m pytest api_v2/tests/test_compare_srd.py::TestCompareClasses api_v2/tests/test_compare_srd.py::TestCompareFeats api_v2/tests/test_compare_srd.py::TestCompareSpecies -v
```
Expected: ImportError or KeyError (field maps not yet configured)

- [ ] **Step 3: Add field maps, skip fields, and runners to `compare_srd.py`**

**3a. Add to `_FIELD_MAPS`** (in the existing dict):

```python
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
```

**3b. Add to `SKIP_FIELDS`** (in the existing dict):

```python
    "classes": {"desc"},
    "feats": {"desc"},
    "species": {"desc"},
```

**3c. Add runner functions** (after the existing runners, before `_RUNNERS`):

```python
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
    # Join Species with their SPEED trait to get a flat DB record
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
```

**3d. Add to `_RUNNERS`** dict:

```python
    "classes": _run_class_comparison,
    "feats": _run_feat_comparison,
    "species": _run_species_comparison,
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
.venv/bin/python -m pytest api_v2/tests/test_compare_srd.py -v
```
Expected: all PASS (136+ tests)

- [ ] **Step 5: Run live comparison against the DB**

```bash
.venv/bin/python manage.py compare_srd --entity classes
.venv/bin/python manage.py compare_srd --entity feats
.venv/bin/python manage.py compare_srd --entity species
```

Expected outputs:
- **classes**: 12 in PDF, 12 in DB, 0 missing, 0 extra, 0 mismatches
- **feats**: 17 in PDF, 17 in DB, 0 missing, 0 extra, 0 mismatches (or a small number of type/prerequisite mismatches worth investigating)
- **species**: 9 in PDF, 9 in DB, 0 missing, 0 extra, 0 or few mismatches

- [ ] **Step 6: Commit**

```bash
git add api_v2/management/commands/compare_srd.py api_v2/tests/test_compare_srd.py
git commit -m "feat: add classes, feats, species comparison to compare_srd"
```

---

## Task 5: Full suite run and final commit

- [ ] **Step 1: Run the full test suite**

```bash
.venv/bin/python -m pytest api_v2/tests/test_srd_parsers.py api_v2/tests/test_compare_srd.py -v
```
Expected: all PASS

- [ ] **Step 2: Run all entities comparison**

```bash
.venv/bin/python manage.py compare_srd --entity all
```
Review the output. Any new mismatches in classes/feats/species are real data issues worth investigating.

- [ ] **Step 3: Final commit if needed**

```bash
git add -A
git commit -m "fix: address any issues found by new entity comparisons"
```
