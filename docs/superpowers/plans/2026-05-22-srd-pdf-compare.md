# SRD PDF Compare Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `manage.py compare_srd` — a management command that extracts entities from the SRD 5.2 PDF using pdfplumber and compares them against the Django ORM, reporting completeness and field-accuracy mismatches with a Rich terminal display.

**Architecture:** pdfplumber extracts all PDF text to a single string in the main thread; per-entity parsers operate on that string in parallel via `ThreadPoolExecutor`; comparison diff logic is pure Python; Rich renders a summary table plus per-type mismatch details.

**Tech Stack:** Python 3.11, Django 5.2, pdfplumber>=0.11, rich>=13, pytest + pytest-django, uv

**Spec:** `docs/superpowers/specs/2026-05-22-srd-pdf-compare-design.md`

---

## File Map

| Action | Path | Responsibility |
|--------|------|---------------|
| Create | `data/raw_sources/srd_5_2/parsers/__init__.py` | Package marker |
| Create | `data/raw_sources/srd_5_2/parsers/base.py` | PDF text extraction, cleaning, slugify, parse_cost, parse_dice |
| Create | `data/raw_sources/srd_5_2/parsers/spells.py` | SpellRecord dataclass + extract_spells() |
| Create | `data/raw_sources/srd_5_2/parsers/creatures.py` | CreatureRecord dataclass + extract_creatures() |
| Create | `data/raw_sources/srd_5_2/parsers/items.py` | WeaponRecord, ArmorRecord, ItemRecord, MagicItemRecord + extractors |
| Create | `api_v2/management/commands/compare_srd.py` | Management command: orchestrate, diff, Rich render |
| Create | `api_v2/tests/test_srd_parsers.py` | Unit tests for all parsers (no DB needed) |
| Create | `api_v2/tests/test_compare_srd.py` | Integration tests for management command |
| Modify | `pyproject.toml` | Add pdfplumber>=0.11 and rich>=13 to dependencies |

---

## Task 0: Dependencies and Directory Setup

**Files:**
- Modify: `pyproject.toml`
- Create: `data/raw_sources/srd_5_2/parsers/__init__.py`

- [ ] **Step 1: Add dependencies**

Edit `pyproject.toml`. In the `dependencies` list (the one under `[project]`, not `dev`), add:

```toml
"pdfplumber>=0.11",
"rich>=13",
```

- [ ] **Step 2: Sync and verify**

```bash
uv sync
python -c "import pdfplumber; import rich; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Create parsers package**

```bash
mkdir -p data/raw_sources/srd_5_2/parsers && touch data/raw_sources/srd_5_2/parsers/__init__.py
```

Note: `api_v2/management/commands/` already exists (contains `import.py` and `export.py`). No `__init__.py` files are needed — Django discovers management commands without them.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml uv.lock data/raw_sources/srd_5_2/parsers/__init__.py
git commit -m "feat: add pdfplumber and rich dependencies, create parsers package"
```

---

## Task 1: Probe PDF Text Format (No Commit — Exploration Only)

Before writing any parser tests, run pdfplumber on the actual PDF and examine the raw output.
This tells you exactly what the text looks like (heading styles, table layout, line endings).

**Files:** None — this is a one-off exploration script, do not commit it.

- [ ] **Step 1: Create probe script**

Create `data/raw_sources/srd_5_2/probe_pdf.py` (DO NOT commit):

```python
"""Run once to understand pdfplumber text extraction format."""
import pdfplumber
import sys

PDF = "data/raw_sources/srd_5_2/SRD_CC_v5.2.pdf"

with pdfplumber.open(PDF) as pdf:
    total = len(pdf.pages)
    print(f"Total pages: {total}\n")

    # Find a spell page (spells are roughly in the second half of the book)
    # Adjust page numbers after seeing results
    print("=== SPELL SAMPLE (pages 180-183) ===")
    for i in range(180, 184):
        p = pdf.pages[i]
        print(f"--- page {i+1} ---")
        print(repr(p.extract_text()[:800]))
        tables = p.extract_tables()
        if tables:
            print(f"  tables on this page: {len(tables)}")
            print(f"  first table: {tables[0][:3]}")
        print()

    print("=== CREATURE SAMPLE (pages 250-253) ===")
    for i in range(250, 254):
        p = pdf.pages[i]
        print(f"--- page {i+1} ---")
        print(repr(p.extract_text()[:800]))
        tables = p.extract_tables()
        if tables:
            print(f"  tables: {tables[0][:3]}")
        print()

    print("=== WEAPON/ITEM SAMPLE (pages 130-133) ===")
    for i in range(130, 134):
        p = pdf.pages[i]
        print(f"--- page {i+1} ---")
        print(repr(p.extract_text()[:600]))
        print()
```

- [ ] **Step 2: Run probe**

```bash
python data/raw_sources/srd_5_2/probe_pdf.py 2>&1 | head -200
```

- [ ] **Step 3: Record findings — answer these questions before proceeding**

  - Do spell names appear on their own line? What exactly precedes/follows them?
  - How does `page.extract_text()` represent the level/school line (e.g., `"2nd-level evocation"` or `"2ND-LEVEL EVOCATION"`)?
  - Are ability score tables extracted as text inline, or only via `extract_tables()`?
  - How does pdfplumber handle multi-column layout (does creature text interleave)?
  - What does a creature name line look like — is it `"Adult Black Dragon"` or `"ADULT BLACK DRAGON"`?

  **Update the sample text strings in Tasks 2–5 tests to match actual pdfplumber output.**
  The sample strings in this plan are based on the markdown files (which mirror PDF content)
  but the exact whitespace/case/delimiter format must be validated against probe output.

- [ ] **Step 4: Delete probe script (do not commit it)**

```bash
rm data/raw_sources/srd_5_2/probe_pdf.py
```

---

## Task 2: base.py Utilities

**Files:**
- Create: `data/raw_sources/srd_5_2/parsers/base.py`
- Create: `api_v2/tests/test_srd_parsers.py`

- [ ] **Step 1: Write failing tests**

Create `api_v2/tests/test_srd_parsers.py`:

```python
"""Tests for SRD PDF parser utilities and section parsers."""
import sys
import os
import pytest

# Make the parsers package importable without installing it
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from data.raw_sources.srd_5_2.parsers.base import (
    clean_text,
    slugify,
    parse_cost,
    parse_dice,
    extract_section,
)


class TestCleanText:
    def test_strips_ligature_fi(self):
        assert clean_text("ﬁreball") == "fireball"

    def test_strips_ligature_fl(self):
        assert clean_text("ﬂame") == "flame"

    def test_strips_soft_hyphen(self):
        assert clean_text("fire\xadball") == "fireball"

    def test_normalizes_whitespace(self):
        assert clean_text("hello   world\n") == "hello world"

    def test_passthrough_normal_text(self):
        assert clean_text("Acid Arrow") == "Acid Arrow"


class TestSlugify:
    def test_lowercases(self):
        assert slugify("Acid Arrow") == "acid-arrow"

    def test_strips_apostrophes(self):
        assert slugify("Tasha's Cauldron") == "tashas-cauldron"

    def test_strips_punctuation(self):
        assert slugify("Fireball!") == "fireball"

    def test_multiple_spaces_become_single_hyphen(self):
        assert slugify("Ball  Lightning") == "ball-lightning"

    def test_already_slugified(self):
        assert slugify("acid-arrow") == "acid-arrow"


class TestParseCost:
    def test_gold(self):
        assert parse_cost("10 gp") == {"amount": 10, "unit": "gp"}

    def test_silver(self):
        assert parse_cost("50 sp") == {"amount": 50, "unit": "sp"}

    def test_copper(self):
        assert parse_cost("2 cp") == {"amount": 2, "unit": "cp"}

    def test_decimal(self):
        assert parse_cost("0.5 gp") == {"amount": 0.5, "unit": "gp"}

    def test_no_match_returns_none(self):
        assert parse_cost("") is None
        assert parse_cost("Free") is None
        assert parse_cost("varies") is None


class TestParseDice:
    def test_basic(self):
        assert parse_dice("2d6") == {"count": 2, "die": 6, "bonus": 0}

    def test_with_positive_bonus(self):
        assert parse_dice("2d6+3") == {"count": 2, "die": 6, "bonus": 3}

    def test_with_negative_bonus(self):
        assert parse_dice("1d8-1") == {"count": 1, "die": 8, "bonus": -1}

    def test_single_die(self):
        assert parse_dice("1d4") == {"count": 1, "die": 4, "bonus": 0}

    def test_large_dice(self):
        assert parse_dice("10d10+30") == {"count": 10, "die": 10, "bonus": 30}

    def test_no_match_returns_none(self):
        assert parse_dice("") is None
        assert parse_dice("some text") is None


class TestExtractSection:
    def test_extracts_between_markers(self):
        text = "INTRO\nSPELLS START\nAcid Arrow stuff\nSPELLS END\nEPILOGUE"
        import re
        result = extract_section(text, re.compile(r"SPELLS START"), re.compile(r"SPELLS END"))
        assert "Acid Arrow stuff" in result
        assert "INTRO" not in result
        assert "EPILOGUE" not in result

    def test_raises_if_start_not_found(self):
        with pytest.raises(ValueError, match="start marker"):
            import re
            extract_section("no markers here", re.compile(r"MISSING"), re.compile(r"END"))

    def test_raises_if_end_not_found(self):
        with pytest.raises(ValueError, match="end marker"):
            import re
            extract_section("START here", re.compile(r"START"), re.compile(r"MISSING"))
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
python -m pytest api_v2/tests/test_srd_parsers.py::TestCleanText api_v2/tests/test_srd_parsers.py::TestSlugify api_v2/tests/test_srd_parsers.py::TestParseCost api_v2/tests/test_srd_parsers.py::TestParseDice api_v2/tests/test_srd_parsers.py::TestExtractSection -v 2>&1 | tail -20
```

Expected: ModuleNotFoundError (base.py doesn't exist yet).

- [ ] **Step 3: Implement base.py**

Create `data/raw_sources/srd_5_2/parsers/base.py`:

```python
"""Shared utilities for SRD PDF parsers."""
from __future__ import annotations
import re
import unicodedata
import pdfplumber

LIGATURE_MAP = {
    "ﬀ": "ff",
    "ﬁ": "fi",
    "ﬂ": "fl",
    "ﬃ": "ffi",
    "ﬄ": "ffl",
}


def clean_text(s: str) -> str:
    """Strip ligatures, soft hyphens, normalize whitespace."""
    for ligature, replacement in LIGATURE_MAP.items():
        s = s.replace(ligature, replacement)
    s = s.replace("\xad", "")  # soft hyphen
    s = unicodedata.normalize("NFC", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def slugify(name: str) -> str:
    """Normalize a name to a URL-safe slug for dict-key matching."""
    s = clean_text(name).lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s+", "-", s.strip())
    s = re.sub(r"-+", "-", s)
    return s


def parse_cost(s: str) -> dict | None:
    """Parse '10 gp' / '5 sp' / '2 cp' into {"amount": float, "unit": str}."""
    m = re.search(r"([\d.]+)\s*(gp|sp|cp)", s, re.IGNORECASE)
    if not m:
        return None
    return {"amount": float(m.group(1)), "unit": m.group(2).lower()}


def parse_dice(s: str) -> dict | None:
    """Parse '2d6+3' into {"count": int, "die": int, "bonus": int}."""
    m = re.search(r"(\d+)d(\d+)([+-]\d+)?", s)
    if not m:
        return None
    return {
        "count": int(m.group(1)),
        "die": int(m.group(2)),
        "bonus": int(m.group(3)) if m.group(3) else 0,
    }


def extract_full_text(pdf_path: str) -> str:
    """Open PDF once, concatenate all page text. Call this in the main thread only."""
    pages: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            pages.append(text)
    return "\n".join(pages)


def extract_section(full_text: str, start_re: re.Pattern, end_re: re.Pattern) -> str:
    """Return the substring of full_text between first match of start_re and end_re."""
    m_start = start_re.search(full_text)
    if not m_start:
        raise ValueError(f"start marker not found: {start_re.pattern!r}")
    m_end = end_re.search(full_text, m_start.end())
    if not m_end:
        raise ValueError(f"end marker not found after start: {end_re.pattern!r}")
    return full_text[m_start.end():m_end.start()]
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
python -m pytest api_v2/tests/test_srd_parsers.py::TestCleanText api_v2/tests/test_srd_parsers.py::TestSlugify api_v2/tests/test_srd_parsers.py::TestParseCost api_v2/tests/test_srd_parsers.py::TestParseDice api_v2/tests/test_srd_parsers.py::TestExtractSection -v 2>&1 | tail -20
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add data/raw_sources/srd_5_2/parsers/base.py api_v2/tests/test_srd_parsers.py
git commit -m "feat: add SRD parser base utilities with tests"
```

---

## Task 3: Spell Parser

**Files:**
- Create: `data/raw_sources/srd_5_2/parsers/spells.py`
- Modify: `api_v2/tests/test_srd_parsers.py`

**Important:** Update the sample text strings below based on Task 1 probe findings before writing tests. The strings shown here mirror the markdown source format; calibrate against actual pdfplumber output.

- [ ] **Step 1: Write failing spell parser tests**

Append to `api_v2/tests/test_srd_parsers.py`:

```python
from data.raw_sources.srd_5_2.parsers.spells import extract_spells, SpellRecord

# Adjust this sample to match actual pdfplumber output from Task 1 probe.
SAMPLE_SPELL_TEXT = """
Chapter 7: Spells

Acid Arrow
2nd-level evocation
Casting Time: 1 action
Range: 90 feet
Components: V, S, M (powdered rhubarb leaf and an adder's stomach)
Duration: Instantaneous
A shimmering green arrow streaks toward a target within range.

At Higher Levels. When you cast this spell using a spell slot of 3rd level or higher...

Aid
2nd-level abjuration
Casting Time: 1 action
Range: 30 feet
Components: V, S, M (a tiny strip of white cloth)
Duration: 8 hours (concentration)
Your spell bolsters your allies with toughness and resolve.

Chapter 8: Monsters
""".strip()


class TestExtractSpells:
    def test_finds_acid_arrow(self):
        spells = extract_spells(SAMPLE_SPELL_TEXT)
        names = [s.name for s in spells]
        assert "Acid Arrow" in names

    def test_finds_aid(self):
        spells = extract_spells(SAMPLE_SPELL_TEXT)
        names = [s.name for s in spells]
        assert "Aid" in names

    def test_spell_level(self):
        spells = {s.name: s for s in extract_spells(SAMPLE_SPELL_TEXT)}
        assert spells["Acid Arrow"].level == 2

    def test_spell_school(self):
        spells = {s.name: s for s in extract_spells(SAMPLE_SPELL_TEXT)}
        assert spells["Acid Arrow"].school == "evocation"

    def test_spell_casting_time(self):
        spells = {s.name: s for s in extract_spells(SAMPLE_SPELL_TEXT)}
        assert spells["Acid Arrow"].casting_time == "1 action"

    def test_spell_range(self):
        spells = {s.name: s for s in extract_spells(SAMPLE_SPELL_TEXT)}
        assert spells["Acid Arrow"].range_text == "90 feet"

    def test_spell_verbal_component(self):
        spells = {s.name: s for s in extract_spells(SAMPLE_SPELL_TEXT)}
        assert spells["Acid Arrow"].verbal is True
        assert spells["Acid Arrow"].somatic is True
        assert spells["Acid Arrow"].material is True

    def test_spell_concentration(self):
        spells = {s.name: s for s in extract_spells(SAMPLE_SPELL_TEXT)}
        # Aid duration is "8 hours (concentration)"
        assert spells["Aid"].concentration is True
        assert spells["Acid Arrow"].concentration is False

    def test_higher_level_extracted(self):
        spells = {s.name: s for s in extract_spells(SAMPLE_SPELL_TEXT)}
        assert spells["Acid Arrow"].higher_level is not None
        assert "3rd level" in spells["Acid Arrow"].higher_level

    def test_sanity_check_raises_on_empty(self):
        with pytest.raises(ValueError, match="fewer than 300"):
            extract_spells("no spells here")
```

- [ ] **Step 2: Run to confirm failure**

```bash
python -m pytest api_v2/tests/test_srd_parsers.py::TestExtractSpells -v 2>&1 | tail -20
```

Expected: ImportError (spells.py doesn't exist yet).

- [ ] **Step 3: Implement spells.py**

Create `data/raw_sources/srd_5_2/parsers/spells.py`:

```python
"""Extract spell records from SRD PDF extracted text."""
from __future__ import annotations
import re
from dataclasses import dataclass
from .base import clean_text, slugify, extract_section

# Regex patterns — calibrate against probe output if needed
_LEVEL_SCHOOL_RE = re.compile(
    r"(cantrip|\d+(?:st|nd|rd|th)-level)\s+(abjuration|conjuration|divination|"
    r"enchantment|evocation|illusion|necromancy|transmutation)",
    re.IGNORECASE,
)
_FIELD_RE = re.compile(
    r"^(Casting Time|Range|Components|Duration):\s*(.+)$", re.MULTILINE
)
_HIGHER_LEVEL_RE = re.compile(
    r"At Higher Levels[.\s]*(.+?)(?=\n[A-Z][a-z]|\Z)", re.DOTALL
)

# Section boundaries — adjust patterns based on Task 1 probe findings
_SECTION_START = re.compile(r"Chapter\s+\d+[:\s]+Spells", re.IGNORECASE)
_SECTION_END = re.compile(r"Chapter\s+\d+[:\s]+(?!Spells)", re.IGNORECASE)

# Spell entry boundary: a line of title-case text not preceded by field labels
_SPELL_NAME_RE = re.compile(
    r"^([A-Z][A-Za-z ''\/\-]+)$", re.MULTILINE
)


@dataclass(frozen=True)
class SpellRecord:
    name: str
    level: int  # 0 = cantrip
    school: str
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


def _parse_level(s: str) -> int:
    if "cantrip" in s.lower():
        return 0
    m = re.search(r"(\d+)", s)
    return int(m.group(1)) if m else 0


def _parse_components(s: str) -> tuple[bool, bool, bool, str | None]:
    verbal = "V" in s.split(",")[0].split("(")[0]
    somatic = "S" in s.split(",")[0:2]
    somatic = bool(re.search(r"\bS\b", s.split("(")[0]))
    material = "M" in s.split("(")[0]
    mat_specified = None
    m = re.search(r"\((.+?)\)", s)
    if m:
        mat_specified = m.group(1).strip()
    return verbal, somatic, material, mat_specified


def extract_spells(full_text: str) -> list[SpellRecord]:
    """Parse all spell records from PDF full text. Raises ValueError if < 300 found."""
    try:
        section = extract_section(full_text, _SECTION_START, _SECTION_END)
    except ValueError:
        section = full_text  # fallback for unit tests with sample text

    records: list[SpellRecord] = []
    # Split section into candidate spell blocks by finding name lines followed by level/school
    blocks = re.split(r"\n(?=[A-Z][A-Za-z ''\/\-]+\n\w+[\w\s-]*level)", section)

    for block in blocks:
        lines = block.strip().splitlines()
        if not lines:
            continue
        name = clean_text(lines[0])
        # Validate: second line must be level+school
        if len(lines) < 2:
            continue
        m = _LEVEL_SCHOOL_RE.search(lines[1])
        if not m:
            continue

        level = _parse_level(m.group(1))
        school = m.group(2).lower()

        fields: dict[str, str] = {}
        for fm in _FIELD_RE.finditer(block):
            fields[fm.group(1)] = fm.group(2).strip()

        components_str = fields.get("Components", "")
        verbal, somatic, material, mat_specified = _parse_components(components_str)

        duration_raw = fields.get("Duration", "")
        concentration = "concentration" in duration_raw.lower()
        ritual = "(ritual)" in block.lower()

        hl_m = _HIGHER_LEVEL_RE.search(block)
        higher_level = clean_text(hl_m.group(1)) if hl_m else None

        records.append(SpellRecord(
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
        ))

    if len(records) < 300:
        raise ValueError(
            f"Spell parser produced only {len(records)} spells — expected ≥300. "
            "Check PDF section boundaries and heading patterns."
        )
    return records
```

> **Note:** This implementation is a starting skeleton. After running against the real PDF
> (Task 1 probe), you will almost certainly need to adjust `_SECTION_START`, `_SECTION_END`,
> and the block-splitting regex to match the actual text format. Iterate until all unit tests
> pass AND a sanity run against the real PDF produces ≥300 spells.

- [ ] **Step 4: Run unit tests**

```bash
python -m pytest api_v2/tests/test_srd_parsers.py::TestExtractSpells -v 2>&1 | tail -30
```

Expected: all PASS.

- [ ] **Step 5: Sanity check against real PDF**

```bash
python -c "
from data.raw_sources.srd_5_2.parsers.base import extract_full_text
from data.raw_sources.srd_5_2.parsers.spells import extract_spells
text = extract_full_text('data/raw_sources/srd_5_2/SRD_CC_v5.2.pdf')
spells = extract_spells(text)
print(f'Extracted {len(spells)} spells')
print('First 5:', [s.name for s in spells[:5]])
print('Last 5:', [s.name for s in spells[-5:]])
"
```

Expected: `Extracted 339 spells` (or close). If counts are wrong, debug the section
boundary regex and block-splitting pattern. Fix until correct, keeping unit tests passing.

- [ ] **Step 6: Commit**

```bash
git add data/raw_sources/srd_5_2/parsers/spells.py api_v2/tests/test_srd_parsers.py
git commit -m "feat: add spell parser with SpellRecord dataclass"
```

---

## Task 4: Creature Parser

**Files:**
- Create: `data/raw_sources/srd_5_2/parsers/creatures.py`
- Modify: `api_v2/tests/test_srd_parsers.py`

**Important:** The creature section is the most format-sensitive. Validate the probe output for multi-column layout and ability score tables before finalizing the sample text below.

If the probe (Task 1) reveals that ability score tables are extracted via `page.extract_tables()` rather than inline text, you will need to modify `extract_full_text()` in `base.py` to also call `page.extract_tables()` per page and insert a sentinel delimiter (e.g., `§TABLE§`) before concatenation. The creature parser can then find and parse the sentinel-delimited table block. Update the `extract_full_text()` implementation and its tests if this is the case.

- [ ] **Step 1: Write failing creature parser tests**

Append to `api_v2/tests/test_srd_parsers.py`:

```python
from data.raw_sources.srd_5_2.parsers.creatures import extract_creatures, CreatureRecord

# Adjust to actual pdfplumber output from Task 1 probe.
# Key question: does the ability score table come through as inline text or require
# extract_tables()? If the latter, this sample won't work as-is.
SAMPLE_CREATURE_TEXT = """
Chapter 9: Monsters

Adult Black Dragon
Huge dragon, chaotic evil
Armor Class: 19 (natural armor)
Hit Points: 195 (17d12 + 85)
Speed: 40 ft., fly 80 ft., swim 40 ft.
STR DEX CON INT WIS CHA
27 (+8) 14 (+2) 25 (+7) 16 (+3) 13 (+1) 17 (+3)
Saving Throws: Dex +7, Con +12, Wis +6, Cha +8
Skills: Perception +11, Stealth +7
Damage Immunities: acid
Senses: blindsight 60 ft., darkvision 120 ft.
Languages: Common, Draconic
Challenge: 17 (18,000 XP)

Banshee
Medium undead, chaotic evil
Armor Class: 12
Hit Points: 58 (13d8)
Speed: 0 ft., fly 40 ft. (hover)
STR DEX CON INT WIS CHA
1 (-5) 14 (+2) 10 (+0) 12 (+1) 11 (+0) 17 (+3)
Damage Resistances: acid, fire, lightning, thunder; bludgeoning, piercing, slashing from nonmagical attacks
Damage Immunities: cold, necrotic, poison
Condition Immunities: charmed, exhaustion, frightened, grappled, paralyzed
Senses: darkvision 60 ft.
Languages: Common, Elvish
Challenge: 4 (1,100 XP)

Chapter 10: Items
""".strip()


class TestExtractCreatures:
    def test_finds_adult_black_dragon(self):
        creatures = extract_creatures(SAMPLE_CREATURE_TEXT)
        names = [c.name for c in creatures]
        assert "Adult Black Dragon" in names

    def test_finds_banshee(self):
        creatures = extract_creatures(SAMPLE_CREATURE_TEXT)
        names = [c.name for c in creatures]
        assert "Banshee" in names

    def test_creature_size_and_type(self):
        creatures = {c.name: c for c in extract_creatures(SAMPLE_CREATURE_TEXT)}
        assert creatures["Adult Black Dragon"].size == "Huge"
        assert creatures["Adult Black Dragon"].type == "dragon"

    def test_creature_armor_class(self):
        creatures = {c.name: c for c in extract_creatures(SAMPLE_CREATURE_TEXT)}
        assert creatures["Adult Black Dragon"].armor_class == 19

    def test_creature_hit_points(self):
        creatures = {c.name: c for c in extract_creatures(SAMPLE_CREATURE_TEXT)}
        assert creatures["Adult Black Dragon"].hit_points == 195

    def test_creature_ability_scores(self):
        creatures = {c.name: c for c in extract_creatures(SAMPLE_CREATURE_TEXT)}
        assert creatures["Adult Black Dragon"].strength == 27
        assert creatures["Adult Black Dragon"].dexterity == 14

    def test_creature_challenge_rating(self):
        creatures = {c.name: c for c in extract_creatures(SAMPLE_CREATURE_TEXT)}
        assert creatures["Adult Black Dragon"].challenge_rating == 17.0
        assert creatures["Banshee"].challenge_rating == 4.0

    def test_creature_walk_speed(self):
        creatures = {c.name: c for c in extract_creatures(SAMPLE_CREATURE_TEXT)}
        assert creatures["Adult Black Dragon"].walk == 40
        assert creatures["Adult Black Dragon"].fly == 80
        assert creatures["Adult Black Dragon"].swim == 40

    def test_creature_damage_immunities(self):
        creatures = {c.name: c for c in extract_creatures(SAMPLE_CREATURE_TEXT)}
        assert "acid" in creatures["Adult Black Dragon"].damage_immunities

    def test_sanity_check_raises_on_empty(self):
        with pytest.raises(ValueError, match="fewer than 250"):
            extract_creatures("no creatures here")
```

- [ ] **Step 2: Run to confirm failure**

```bash
python -m pytest api_v2/tests/test_srd_parsers.py::TestExtractCreatures -v 2>&1 | tail -20
```

Expected: ImportError.

- [ ] **Step 3: Implement creatures.py**

Create `data/raw_sources/srd_5_2/parsers/creatures.py`:

```python
"""Extract creature records from SRD PDF extracted text."""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from .base import clean_text, slugify, extract_section, parse_dice

_SECTION_START = re.compile(r"Chapter\s+\d+[:\s]+Monsters", re.IGNORECASE)
_SECTION_END = re.compile(r"Chapter\s+\d+[:\s]+(?!Monsters)", re.IGNORECASE)

# Two-line entry boundary: title-case name followed by size+type line
_ENTRY_RE = re.compile(
    r"^([A-Z][A-Za-z '\-]+)\n"
    r"(Tiny|Small|Medium|Large|Huge|Gargantuan)\s+(\w+),\s*(.+?)$",
    re.MULTILINE,
)
_AC_RE = re.compile(r"Armor Class:\s*(\d+)")
_HP_RE = re.compile(r"Hit Points:\s*(\d+)")
_HD_RE = re.compile(r"Hit Points:\s*\d+\s*\(([^)]+)\)")
_SPEED_RE = re.compile(r"Speed:\s*(.+?)$", re.MULTILINE)
_ABILITY_RE = re.compile(
    # Scores may appear as "27 (+8) 14 (+2)..." or "27 14 25..." on a single line.
    # Each score is a bare integer optionally followed by a parenthesized modifier.
    # Do NOT use [^0-9]+ between groups — (+8) contains digits.
    r"STR\s+DEX\s+CON\s+INT\s+WIS\s+CHA[^\n]*\n\s*"
    r"(\d+)\s*(?:\([+-]\d+\))?\s+"
    r"(\d+)\s*(?:\([+-]\d+\))?\s+"
    r"(\d+)\s*(?:\([+-]\d+\))?\s+"
    r"(\d+)\s*(?:\([+-]\d+\))?\s+"
    r"(\d+)\s*(?:\([+-]\d+\))?\s+"
    r"(\d+)\s*(?:\([+-]\d+\))?"
)
_CR_RE = re.compile(r"Challenge:\s*([\d/]+)")
_DAMAGE_IMMUNITIES_RE = re.compile(r"Damage Immunities:\s*(.+?)$", re.MULTILINE)
_DAMAGE_RESISTANCES_RE = re.compile(r"Damage Resistances:\s*(.+?)$", re.MULTILINE)
_DAMAGE_VULNERABILITIES_RE = re.compile(r"Damage Vulnerabilities:\s*(.+?)$", re.MULTILINE)
_CONDITION_IMMUNITIES_RE = re.compile(r"Condition Immunities:\s*(.+?)$", re.MULTILINE)
_DARKVISION_RE = re.compile(r"darkvision\s*(\d+)")
_BLINDSIGHT_RE = re.compile(r"blindsight\s*(\d+)")
_TRUESIGHT_RE = re.compile(r"truesight\s*(\d+)")


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
    if "/" in s:
        num, den = s.split("/")
        return int(num) / int(den)
    return float(s)


def _parse_speed(s: str) -> dict:
    result = {"walk": 0, "fly": None, "swim": None, "burrow": None, "climb": None, "hover": False}
    for part in s.split(","):
        part = part.strip()
        m = re.search(r"(\d+)\s*ft", part)
        if not m:
            continue
        v = int(m.group(1))
        if "fly" in part:
            result["fly"] = v
            result["hover"] = "hover" in part.lower()
        elif "swim" in part:
            result["swim"] = v
        elif "burrow" in part:
            result["burrow"] = v
        elif "climb" in part:
            result["climb"] = v
        else:
            result["walk"] = v
    return result


def _parse_list(m: re.Match | None) -> tuple[str, ...]:
    if not m:
        return ()
    raw = m.group(1)
    # Strip "from nonmagical attacks" qualifiers for simple type matching
    raw = re.sub(r";.*", "", raw)
    return tuple(t.strip().lower() for t in raw.split(",") if t.strip())


def extract_creatures(full_text: str) -> list[CreatureRecord]:
    """Parse all creature records from PDF full text. Raises ValueError if < 250 found."""
    try:
        section = extract_section(full_text, _SECTION_START, _SECTION_END)
    except ValueError:
        section = full_text

    # Split on creature entry boundaries
    entry_starts = [(m.start(), m) for m in _ENTRY_RE.finditer(section)]
    records: list[CreatureRecord] = []

    for i, (start, m) in enumerate(entry_starts):
        end = entry_starts[i + 1][0] if i + 1 < len(entry_starts) else len(section)
        block = section[start:end]

        name = clean_text(m.group(1))
        size = m.group(2)
        creature_type = m.group(3).lower()
        alignment = clean_text(m.group(4))

        ac_m = _AC_RE.search(block)
        hp_m = _HP_RE.search(block)
        hd_m = _HD_RE.search(block)
        speed_m = _SPEED_RE.search(block)
        ability_m = _ABILITY_RE.search(block)
        cr_m = _CR_RE.search(block)

        if not all([ac_m, hp_m, speed_m, cr_m]):
            continue  # skip malformed entries

        speed = _parse_speed(speed_m.group(1)) if speed_m else {}

        str_, dex, con, int_, wis, cha = (10, 10, 10, 10, 10, 10)
        if ability_m:
            str_, dex, con, int_, wis, cha = [int(ability_m.group(i)) for i in range(1, 7)]

        records.append(CreatureRecord(
            name=name,
            size=size,
            type=creature_type,
            alignment=alignment,
            armor_class=int(ac_m.group(1)),
            hit_points=int(hp_m.group(1)),
            hit_dice=hd_m.group(1).strip() if hd_m else "",
            walk=speed.get("walk", 0),
            fly=speed.get("fly"),
            swim=speed.get("swim"),
            burrow=speed.get("burrow"),
            climb=speed.get("climb"),
            hover=speed.get("hover", False),
            strength=str_,
            dexterity=dex,
            constitution=con,
            intelligence=int_,
            wisdom=wis,
            charisma=cha,
            challenge_rating=_parse_cr(cr_m.group(1)),
            damage_immunities=_parse_list(_DAMAGE_IMMUNITIES_RE.search(block)),
            damage_resistances=_parse_list(_DAMAGE_RESISTANCES_RE.search(block)),
            damage_vulnerabilities=_parse_list(_DAMAGE_VULNERABILITIES_RE.search(block)),
            condition_immunities=_parse_list(_CONDITION_IMMUNITIES_RE.search(block)),
            darkvision_range=int(m.group(1)) if (m := _DARKVISION_RE.search(block)) else 0,
            blindsight_range=int(m.group(1)) if (m := _BLINDSIGHT_RE.search(block)) else 0,
            truesight_range=int(m.group(1)) if (m := _TRUESIGHT_RE.search(block)) else 0,
        ))

    if len(records) < 250:
        raise ValueError(
            f"Creature parser produced only {len(records)} creatures — expected ≥250."
        )
    return records
```

- [ ] **Step 4: Run unit tests**

```bash
python -m pytest api_v2/tests/test_srd_parsers.py::TestExtractCreatures -v 2>&1 | tail -30
```

Expected: all PASS.

- [ ] **Step 5: Sanity check against real PDF**

```bash
python -c "
from data.raw_sources.srd_5_2.parsers.base import extract_full_text
from data.raw_sources.srd_5_2.parsers.creatures import extract_creatures
text = extract_full_text('data/raw_sources/srd_5_2/SRD_CC_v5.2.pdf')
creatures = extract_creatures(text)
print(f'Extracted {len(creatures)} creatures')
print('First 5:', [c.name for c in creatures[:5]])
"
```

Expected: ≥250 creatures. Iterate on regex patterns until counts match the DB (330).

- [ ] **Step 6: Commit**

```bash
git add data/raw_sources/srd_5_2/parsers/creatures.py api_v2/tests/test_srd_parsers.py
git commit -m "feat: add creature parser with CreatureRecord dataclass"
```

---

## Task 5: Item Parsers

**Files:**
- Create: `data/raw_sources/srd_5_2/parsers/items.py`
- Modify: `api_v2/tests/test_srd_parsers.py`

- [ ] **Step 1: Write failing item parser tests**

Append to `api_v2/tests/test_srd_parsers.py`:

```python
from data.raw_sources.srd_5_2.parsers.items import (
    extract_weapons, extract_armor, extract_items, extract_magic_items,
    WeaponRecord, ArmorRecord, ItemRecord, MagicItemRecord,
)

SAMPLE_WEAPON_TEXT = """
Chapter 6: Equipment - Weapons

Dagger
Cost: 2 gp
Damage: 1d4 piercing
Weight: 1 lb.
Properties: Finesse, light, thrown
Mastery: Nick

Longsword
Cost: 15 gp
Damage: 1d8 slashing
Weight: 3 lb.
Properties: Versatile (1d10)
Mastery: Sap

Chapter 7: Armor
""".strip()

SAMPLE_ARMOR_TEXT = """
Chapter 7: Armor

Chain Mail
Cost: 75 gp
AC Base: 16
AC Add Dex: False
Strength Required: 13
Stealth Disadvantage: True

Leather
Cost: 10 gp
AC Base: 11
AC Add Dex: True
AC Cap Dex: None
Strength Required: None
Stealth Disadvantage: False

Chapter 8: Magic Items
""".strip()

SAMPLE_ITEMS_TEXT = """
Chapter 5: Equipment

Abacus (2 gp)
A counting device used by merchants. Weight: 2 lb.

Ball Bearings (1 gp)
Bag of 1,000 ball bearings. Weight: 2 lb.

Blanket (5 sp)
A wool blanket. Weight: 3 lb.

Chapter 6: Magic Items
""".strip()


class TestExtractItems:
    def test_finds_abacus(self):
        items = extract_items(SAMPLE_ITEMS_TEXT)
        names = [i.name for i in items]
        assert "Abacus" in names

    def test_item_cost(self):
        items = {i.name: i for i in extract_items(SAMPLE_ITEMS_TEXT)}
        assert items["Abacus"].cost == {"amount": 2.0, "unit": "gp"}

    def test_silver_cost(self):
        items = {i.name: i for i in extract_items(SAMPLE_ITEMS_TEXT)}
        assert items["Blanket"].cost == {"amount": 5.0, "unit": "sp"}

    def test_sanity_check_raises_on_empty(self):
        with pytest.raises(ValueError, match="fewer than 150"):
            extract_items("no items here")


SAMPLE_MAGIC_ITEM_TEXT = """
Chapter 8: Magic Items

Bag of Holding
Wondrous Item, uncommon
This bag has an interior space considerably larger than its outside dimensions.

Cloak of Protection
Cloak, uncommon (requires attunement)
You gain a +1 bonus to AC and saving throws while you wear this cloak.

Chapter 9: Spells
""".strip()


class TestExtractWeapons:
    def test_finds_dagger(self):
        weapons = extract_weapons(SAMPLE_WEAPON_TEXT)
        names = [w.name for w in weapons]
        assert "Dagger" in names

    def test_weapon_cost(self):
        weapons = {w.name: w for w in extract_weapons(SAMPLE_WEAPON_TEXT)}
        assert weapons["Dagger"].cost == {"amount": 2.0, "unit": "gp"}

    def test_weapon_damage_dice(self):
        weapons = {w.name: w for w in extract_weapons(SAMPLE_WEAPON_TEXT)}
        assert weapons["Dagger"].damage == {"count": 1, "die": 4, "bonus": 0}

    def test_sanity_check_raises_on_empty(self):
        with pytest.raises(ValueError, match="fewer than 30"):
            extract_weapons("no weapons here")


class TestExtractArmor:
    def test_finds_chain_mail(self):
        armor = extract_armor(SAMPLE_ARMOR_TEXT)
        names = [a.name for a in armor]
        assert "Chain Mail" in names

    def test_armor_ac_base(self):
        armor = {a.name: a for a in extract_armor(SAMPLE_ARMOR_TEXT)}
        assert armor["Chain Mail"].ac_base == 16
        assert armor["Chain Mail"].strength_required == 13
        assert armor["Chain Mail"].stealth_disadvantage is True
        assert armor["Chain Mail"].ac_add_dex is False

    def test_sanity_check_raises_on_empty(self):
        with pytest.raises(ValueError, match="fewer than 10"):
            extract_armor("no armor here")


class TestExtractMagicItems:
    def test_finds_bag_of_holding(self):
        items = extract_magic_items(SAMPLE_MAGIC_ITEM_TEXT)
        names = [i.name for i in items]
        assert "Bag of Holding" in names

    def test_magic_item_rarity(self):
        items = {i.name: i for i in extract_magic_items(SAMPLE_MAGIC_ITEM_TEXT)}
        assert items["Bag of Holding"].rarity == "uncommon"

    def test_magic_item_attunement(self):
        items = {i.name: i for i in extract_magic_items(SAMPLE_MAGIC_ITEM_TEXT)}
        assert items["Bag of Holding"].requires_attunement is False
        assert items["Cloak of Protection"].requires_attunement is True

    def test_sanity_check_raises_on_empty(self):
        with pytest.raises(ValueError, match="fewer than 700"):
            extract_magic_items("no items here")
```

- [ ] **Step 2: Run to confirm failure**

```bash
python -m pytest api_v2/tests/test_srd_parsers.py::TestExtractWeapons api_v2/tests/test_srd_parsers.py::TestExtractArmor api_v2/tests/test_srd_parsers.py::TestExtractItems api_v2/tests/test_srd_parsers.py::TestExtractMagicItems -v 2>&1 | tail -20
```

Expected: ImportError.

- [ ] **Step 3: Implement items.py**

Create `data/raw_sources/srd_5_2/parsers/items.py`:

```python
"""Extract item records from SRD PDF extracted text."""
from __future__ import annotations
import re
from dataclasses import dataclass
from .base import clean_text, parse_cost, parse_dice, extract_section

# Section boundary patterns — adjust from Task 1 probe
_WEAPON_SECTION_START = re.compile(r"Chapter\s+\d+[:\s]+Equipment[^\n]*Weapon", re.IGNORECASE)
_WEAPON_SECTION_END = re.compile(r"Chapter\s+\d+[:\s]+(?:Armor|Magic)", re.IGNORECASE)
_ARMOR_SECTION_START = re.compile(r"Chapter\s+\d+[:\s]+Armor", re.IGNORECASE)
_ARMOR_SECTION_END = re.compile(r"Chapter\s+\d+[:\s]+(?:Magic|Spell)", re.IGNORECASE)
_MAGIC_SECTION_START = re.compile(r"Chapter\s+\d+[:\s]+Magic Items", re.IGNORECASE)
_MAGIC_SECTION_END = re.compile(r"Chapter\s+\d+[:\s]+(?!Magic)", re.IGNORECASE)

_ITEM_ENTRY_RE = re.compile(r"^([A-Z][A-Za-z '\-,]+)\n(?=Cost:|AC Base:|Wondrous|Armor|Weapon|Ring|Rod|Staff|Wand|Potion|Scroll)", re.MULTILINE)
_MAGIC_ENTRY_RE = re.compile(r"^([A-Z][A-Za-z '\-,()]+)\n(.+?(?:uncommon|common|rare|very rare|legendary|artifact))", re.MULTILINE | re.IGNORECASE)


@dataclass(frozen=True)
class WeaponRecord:
    name: str
    cost: dict | None
    damage: dict | None
    damage_type: str


@dataclass(frozen=True)
class ArmorRecord:
    name: str
    cost: dict | None
    ac_base: int
    ac_add_dex: bool
    ac_cap_dex: int | None
    strength_required: int | None
    stealth_disadvantage: bool


@dataclass(frozen=True)
class ItemRecord:
    name: str
    cost: dict | None
    weight: str


@dataclass(frozen=True)
class MagicItemRecord:
    name: str
    rarity: str
    requires_attunement: bool


_RARITIES = {"common", "uncommon", "rare", "very rare", "legendary", "artifact"}


def extract_weapons(full_text: str) -> list[WeaponRecord]:
    try:
        section = extract_section(full_text, _WEAPON_SECTION_START, _WEAPON_SECTION_END)
    except ValueError:
        section = full_text

    records: list[WeaponRecord] = []
    # Split on weapon name lines
    blocks = re.split(r"\n(?=[A-Z][A-Za-z '\-,]+\nCost:)", section)
    for block in blocks:
        lines = block.strip().splitlines()
        if not lines or not re.search(r"Cost:", block):
            continue
        name = clean_text(lines[0])
        cost = None
        damage = None
        damage_type = ""
        for line in lines[1:]:
            if line.startswith("Cost:"):
                cost = parse_cost(line.split(":", 1)[1].strip())
            elif line.startswith("Damage:"):
                raw = line.split(":", 1)[1].strip()
                damage = parse_dice(raw)
                m = re.search(r"(bludgeoning|piercing|slashing)", raw, re.IGNORECASE)
                damage_type = m.group(1).lower() if m else ""
        if name and (cost or damage):
            records.append(WeaponRecord(name=name, cost=cost, damage=damage, damage_type=damage_type))

    if len(records) < 30:
        raise ValueError(f"Weapon parser produced only {len(records)} weapons — expected ≥30.")
    return records


def extract_armor(full_text: str) -> list[ArmorRecord]:
    try:
        section = extract_section(full_text, _ARMOR_SECTION_START, _ARMOR_SECTION_END)
    except ValueError:
        section = full_text

    records: list[ArmorRecord] = []
    blocks = re.split(r"\n(?=[A-Z][A-Za-z '\-,]+\nCost:)", section)
    for block in blocks:
        lines = block.strip().splitlines()
        if not lines or "AC Base:" not in block:
            continue
        name = clean_text(lines[0])
        fields: dict[str, str] = {}
        for line in lines[1:]:
            if ":" in line:
                k, _, v = line.partition(":")
                fields[k.strip()] = v.strip()

        def _int_or_none(s: str) -> int | None:
            s = s.strip()
            return None if s.lower() in ("none", "") else int(s)

        def _bool_val(s: str) -> bool:
            return s.strip().lower() == "true"

        records.append(ArmorRecord(
            name=name,
            cost=parse_cost(fields.get("Cost", "")),
            ac_base=int(fields.get("AC Base", "0")),
            ac_add_dex=_bool_val(fields.get("AC Add Dex", "False")),
            ac_cap_dex=_int_or_none(fields.get("AC Cap Dex", "None")),
            strength_required=_int_or_none(fields.get("Strength Required", "None")),
            stealth_disadvantage=_bool_val(fields.get("Stealth Disadvantage", "False")),
        ))

    if len(records) < 10:
        raise ValueError(f"Armor parser produced only {len(records)} armor entries — expected ≥10.")
    return records


def extract_items(full_text: str) -> list[ItemRecord]:
    """Parse adventuring gear / general items."""
    records: list[ItemRecord] = []
    # Items are spread across multiple sections; use a broad search
    for m in re.finditer(r"^([A-Z][A-Za-z '\-,]+)\s*\(([^)]+)\)", full_text, re.MULTILINE):
        cost_raw = m.group(2)
        cost = parse_cost(cost_raw)
        if cost:
            records.append(ItemRecord(name=clean_text(m.group(1)), cost=cost, weight=""))
    if len(records) < 150:
        raise ValueError(f"Item parser produced only {len(records)} items — expected ≥150.")
    return records


def extract_magic_items(full_text: str) -> list[MagicItemRecord]:
    try:
        section = extract_section(full_text, _MAGIC_SECTION_START, _MAGIC_SECTION_END)
    except ValueError:
        section = full_text

    records: list[MagicItemRecord] = []
    for m in _MAGIC_ENTRY_RE.finditer(section):
        name = clean_text(m.group(1))
        line2 = m.group(2).lower()
        rarity = next((r for r in sorted(_RARITIES, key=len, reverse=True) if r in line2), "common")
        requires_attunement = "requires attunement" in line2
        records.append(MagicItemRecord(name=name, rarity=rarity, requires_attunement=requires_attunement))

    if len(records) < 700:
        raise ValueError(f"Magic item parser produced only {len(records)} items — expected ≥700.")
    return records
```

- [ ] **Step 4: Run unit tests**

```bash
python -m pytest api_v2/tests/test_srd_parsers.py::TestExtractWeapons api_v2/tests/test_srd_parsers.py::TestExtractArmor api_v2/tests/test_srd_parsers.py::TestExtractItems api_v2/tests/test_srd_parsers.py::TestExtractMagicItems -v 2>&1 | tail -30
```

Expected: all PASS.

- [ ] **Step 5: Sanity check against real PDF**

```bash
python -c "
from data.raw_sources.srd_5_2.parsers.base import extract_full_text
from data.raw_sources.srd_5_2.parsers.items import extract_weapons, extract_armor, extract_magic_items
text = extract_full_text('data/raw_sources/srd_5_2/SRD_CC_v5.2.pdf')
print('Weapons:', len(extract_weapons(text)))
print('Armor:', len(extract_armor(text)))
print('Magic items:', len(extract_magic_items(text)))
"
```

Expected: Weapons ≥30, Armor ≥10, Magic items ≥700. Iterate on patterns until counts match DB.

- [ ] **Step 6: Commit**

```bash
git add data/raw_sources/srd_5_2/parsers/items.py api_v2/tests/test_srd_parsers.py
git commit -m "feat: add weapon, armor, and magic item parsers"
```

---

## Task 6: Management Command

**Files:**
- Create: `api_v2/management/commands/compare_srd.py`
- Create: `api_v2/tests/test_compare_srd.py`

- [ ] **Step 1: Write failing management command tests**

Create `api_v2/tests/test_compare_srd.py`:

```python
"""Tests for the compare_srd management command."""
import pytest
from unittest.mock import patch
from io import StringIO
from django.test import TestCase
from django.core.management import call_command
from api_v2.management.commands.compare_srd import (
    compare_records,
    FieldMismatch,
    ComparisonResult,
)
from data.raw_sources.srd_5_2.parsers.spells import SpellRecord


class TestCompareRecords:
    """Test the pure diff logic without DB or PDF."""

    def _make_spell(self, name, level=1, school="evocation"):
        return SpellRecord(
            name=name, level=level, school=school,
            casting_time="1 action", range_text="60 feet",
            verbal=True, somatic=True, material=False,
            material_specified=None, duration="Instantaneous",
            concentration=False, ritual=False, higher_level=None,
        )

    def test_matching_records_produce_no_mismatches(self):
        pdf = [self._make_spell("Fireball", level=3)]
        db = [{"name": "Fireball", "level": 3, "school__name": "evocation",
               "casting_time": "1 action", "range_text": "60 feet",
               "verbal": True, "somatic": True, "material": False,
               "duration": "Instantaneous", "concentration": False, "ritual": False}]
        result = compare_records("spells", pdf, db, skip_fields={"higher_level", "material_specified"})
        assert result.missing == []
        assert result.extra == []
        assert result.mismatches == []

    def test_detects_missing_in_db(self):
        pdf = [self._make_spell("Fireball"), self._make_spell("Acid Arrow")]
        db = [{"name": "Fireball", "level": 1, "school__name": "evocation",
               "casting_time": "1 action", "range_text": "60 feet",
               "verbal": True, "somatic": True, "material": False,
               "duration": "Instantaneous", "concentration": False, "ritual": False}]
        result = compare_records("spells", pdf, db, skip_fields={"higher_level", "material_specified"})
        assert "Acid Arrow" in result.missing

    def test_detects_extra_in_db(self):
        pdf = [self._make_spell("Fireball")]
        db = [
            {"name": "Fireball", "level": 1, "school__name": "evocation",
             "casting_time": "1 action", "range_text": "60 feet",
             "verbal": True, "somatic": True, "material": False,
             "duration": "Instantaneous", "concentration": False, "ritual": False},
            {"name": "Bonus Spell", "level": 1, "school__name": "evocation",
             "casting_time": "1 action", "range_text": "60 feet",
             "verbal": True, "somatic": True, "material": False,
             "duration": "Instantaneous", "concentration": False, "ritual": False},
        ]
        result = compare_records("spells", pdf, db, skip_fields={"higher_level", "material_specified"})
        assert "Bonus Spell" in result.extra

    def test_detects_field_mismatch(self):
        pdf = [self._make_spell("Fireball", level=3)]
        db = [{"name": "Fireball", "level": 9, "school__name": "evocation",
               "casting_time": "1 action", "range_text": "60 feet",
               "verbal": True, "somatic": True, "material": False,
               "duration": "Instantaneous", "concentration": False, "ritual": False}]
        result = compare_records("spells", pdf, db, skip_fields={"higher_level", "material_specified"})
        assert any(m.field == "level" and m.pdf_value == 3 and m.db_value == 9
                   for m in result.mismatches)

    def test_skip_fields_are_excluded(self):
        pdf = [self._make_spell("Fireball")]
        db = [{"name": "Fireball", "level": 1, "school__name": "evocation",
               "casting_time": "1 action", "range_text": "60 feet",
               "verbal": True, "somatic": True, "material": False,
               "duration": "COMPLETELY DIFFERENT",  # this field is skipped
               "concentration": False, "ritual": False}]
        result = compare_records("spells", pdf, db, skip_fields={"duration", "higher_level", "material_specified"})
        assert result.mismatches == []
```

- [ ] **Step 2: Run to confirm failure**

```bash
python -m pytest api_v2/tests/test_compare_srd.py::TestCompareRecords -v 2>&1 | tail -20
```

Expected: ImportError.

- [ ] **Step 3: Implement compare_srd.py**

Create `api_v2/management/commands/compare_srd.py`:

```python
"""Management command: compare SRD PDF content against the database."""
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

from data.raw_sources.srd_5_2.parsers.base import extract_full_text, slugify, clean_text
from data.raw_sources.srd_5_2.parsers.spells import extract_spells, SpellRecord
from data.raw_sources.srd_5_2.parsers.creatures import extract_creatures, CreatureRecord
from data.raw_sources.srd_5_2.parsers.items import (
    extract_weapons, extract_armor, extract_magic_items,
    WeaponRecord, ArmorRecord, MagicItemRecord,
)

DEFAULT_PDF = os.path.join(
    os.path.dirname(__file__),
    "../../../../data/raw_sources/srd_5_2/SRD_CC_v5.2.pdf",
)

# Fields skipped per entity type (formatting/prose differences expected)
SKIP_FIELDS: dict[str, set[str]] = {
    "spells": {"desc", "higher_level", "material_specified"},
    "creatures": {"desc", "traits", "actions"},
    "weapons": {"desc", "mastery_desc"},
    "armor": {"desc"},
    "magic_items": {"desc"},
}

# ORM field mapping: maps parser record field → DB values() key
# Note: Spell has both range_text (TextField, human-readable e.g. "90 feet") and
# range (distance field, numeric). We compare range_text — the PDF value
# is a string like "90 feet" and range_text is the correct counterpart.
SPELL_FIELD_MAP = {
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
}


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


def _normalize(value: Any) -> Any:
    """Normalize a value for comparison."""
    if isinstance(value, str):
        return clean_text(value).lower().strip()
    if isinstance(value, list):
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
    """Pure diff logic: compare PDF records against DB records by slugified name."""
    pdf_by_slug = {slugify(r.name): r for r in pdf_records}
    db_by_slug = {slugify(r["name"]): r for r in db_records}

    missing = [pdf_by_slug[s].name for s in pdf_by_slug if s not in db_by_slug]
    extra = [db_by_slug[s]["name"] for s in db_by_slug if s not in pdf_by_slug]

    mismatches: list[FieldMismatch] = []
    for slug in pdf_by_slug:
        if slug not in db_by_slug:
            continue
        pdf_rec = pdf_by_slug[slug]
        db_rec = db_by_slug[slug]
        for field, db_key in _field_map_for(entity_type).items():
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
        missing=sorted(missing),
        extra=sorted(extra),
        mismatches=mismatches,
    )


def _field_map_for(entity_type: str) -> dict[str, str]:
    maps = {
        "spells": SPELL_FIELD_MAP,
        "creatures": {
            "armor_class": "armor_class", "hit_points": "hit_points",
            "strength": "ability_score_strength", "dexterity": "ability_score_dexterity",
            "constitution": "ability_score_constitution", "intelligence": "ability_score_intelligence",
            "wisdom": "ability_score_wisdom", "charisma": "ability_score_charisma",
            "challenge_rating": "challenge_rating",
            "walk": "walk", "fly": "fly", "swim": "swim", "burrow": "burrow", "climb": "climb",
        },
        # damage_type and rarity are ForeignKeys — use double-underscore traversal
        "weapons": {"damage_type": "damage_type__name"},
        "armor": {
            "ac_base": "ac_base", "ac_add_dex": "ac_add_dexmod",
            "strength_required": "strength_score_required",
            "stealth_disadvantage": "grants_stealth_disadvantage",
        },
        "magic_items": {"rarity": "rarity__name", "requires_attunement": "requires_attunement"},
    }
    return maps.get(entity_type, {})


def _run_spell_comparison(full_text: str, document: str) -> ComparisonResult:
    from api_v2.models import Spell
    pdf_records = extract_spells(full_text)
    db_records = list(Spell.objects.filter(document_id=document).values(
        "name", "level", "school__name", "casting_time", "range_text",
        "verbal", "somatic", "material", "duration", "concentration", "ritual",
    ))
    return compare_records("spells", pdf_records, db_records, SKIP_FIELDS["spells"])


def _run_creature_comparison(full_text: str, document: str) -> ComparisonResult:
    from api_v2.models import Creature
    pdf_records = extract_creatures(full_text)
    db_records = list(Creature.objects.filter(document_id=document).values(
        "name", "armor_class", "hit_points", "hit_dice", "challenge_rating",
        "ability_score_strength", "ability_score_dexterity", "ability_score_constitution",
        "ability_score_intelligence", "ability_score_wisdom", "ability_score_charisma",
        "walk", "fly", "swim", "burrow", "climb",
    ))
    return compare_records("creatures", pdf_records, db_records, SKIP_FIELDS["creatures"])


def _run_weapon_comparison(full_text: str, document: str) -> ComparisonResult:
    from api_v2.models import Weapon
    pdf_records = extract_weapons(full_text)
    # damage_type is a ForeignKey — use double-underscore to get the string name
    db_records = list(Weapon.objects.filter(document_id=document).values("name", "damage_type__name"))
    return compare_records("weapons", pdf_records, db_records, SKIP_FIELDS["weapons"])


def _run_armor_comparison(full_text: str, document: str) -> ComparisonResult:
    from api_v2.models import Armor
    pdf_records = extract_armor(full_text)
    db_records = list(Armor.objects.filter(document_id=document).values(
        "name", "ac_base", "ac_add_dexmod", "strength_score_required", "grants_stealth_disadvantage",
    ))
    return compare_records("armor", pdf_records, db_records, SKIP_FIELDS["armor"])


def _run_magic_item_comparison(full_text: str, document: str) -> ComparisonResult:
    from api_v2.models import MagicItem
    pdf_records = extract_magic_items(full_text)
    # rarity is a ForeignKey — use double-underscore to get the string name
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


def _render_results(results: dict[str, ComparisonResult], elapsed: float) -> None:
    console = Console()

    summary = Table(title=f"SRD 5.2 PDF vs Database  (completed in {elapsed:.1f}s)")
    summary.add_column("Entity type", style="bold")
    summary.add_column("In PDF", justify="right")
    summary.add_column("In DB", justify="right")
    summary.add_column("Missing", justify="right", style="red")
    summary.add_column("Extra", justify="right", style="yellow")
    summary.add_column("Mismatches", justify="right", style="yellow")

    for name, result in results.items():
        missing_str = str(len(result.missing)) if result.missing else "[green]0[/green]"
        extra_str = str(len(result.extra)) if result.extra else "[green]0[/green]"
        mismatch_str = str(len(result.mismatches)) if result.mismatches else "[green]0[/green]"
        summary.add_row(
            name, str(result.pdf_count), str(result.db_count),
            missing_str, extra_str, mismatch_str,
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


class Command(BaseCommand):
    help = "Compare SRD PDF content against the database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--pdf",
            default=os.path.normpath(DEFAULT_PDF),
            help="Path to SRD PDF file.",
        )
        parser.add_argument("--document", default="srd-2024", help="Document slug to compare against.")
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

        self.stdout.write(f"Extracting text from {pdf_path}...")
        full_text = extract_full_text(pdf_path)

        entity_types = list(_RUNNERS.keys()) if entity == "all" else [entity]

        start = time.monotonic()
        results: dict[str, ComparisonResult] = {}

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(_RUNNERS[etype], full_text, document): etype
                for etype in entity_types
            }
            for future in concurrent.futures.as_completed(futures):
                etype = futures[future]
                try:
                    results[etype] = future.result()
                except Exception as exc:
                    self.stderr.write(f"  ERROR comparing {etype}: {exc}")

        elapsed = time.monotonic() - start
        _render_results({k: results[k] for k in entity_types if k in results}, elapsed)
```

- [ ] **Step 4: Run unit tests**

```bash
python -m pytest api_v2/tests/test_compare_srd.py::TestCompareRecords -v 2>&1 | tail -30
```

Expected: all PASS.

- [ ] **Step 5: Smoke test against real PDF and live DB**

First ensure the DB is populated:

```bash
python manage.py import -d data/v2/wizards-of-the-coast/srd-2024
```

Then run the compare:

```bash
python manage.py compare_srd --entity spells
```

Expected: summary table with spell counts, any mismatches listed. Runtime < 10 seconds.

```bash
python manage.py compare_srd  # all entity types
```

- [ ] **Step 6: Fix any ORM field name mismatches**

If the command errors with `FieldError` (unknown field), check the actual model field names in:
- `api_v2/models/spell.py` for spell fields
- `api_v2/models/abstracts.py` for ability score and saving throw fields
- `api_v2/models/speed.py` for speed fields (`walk`, `fly`, etc.)
- `api_v2/models/object.py` for `armor_class`, `hit_points`, `hit_dice`
- `api_v2/models/weapon.py` for weapon fields
- `api_v2/models/armor.py` for armor fields

Update `_field_map_for()` and the `values()` calls in `_run_*` functions to match.

- [ ] **Step 7: Commit**

```bash
git add api_v2/management/commands/compare_srd.py api_v2/tests/test_compare_srd.py
git commit -m "feat: add compare_srd management command with Rich terminal output"
```

---

## Verification

After all tasks are complete:

```bash
# Run all parser unit tests
python -m pytest api_v2/tests/test_srd_parsers.py api_v2/tests/test_compare_srd.py -v

# Full compare against live DB
python manage.py compare_srd

# Single entity type
python manage.py compare_srd --entity spells

# Different document slug (future use)
python manage.py compare_srd --document srd-2014
```

Expected:
- All unit tests PASS
- Full compare completes in under 10 seconds
- Zero missing records for a correctly imported document
- Any field mismatches are real data quality issues in the fixtures (investigate and fix upstream)
