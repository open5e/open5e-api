"""Tests for SRD PDF parser utilities and section parsers."""
import sys
import os
import pytest
from unittest.mock import patch, MagicMock

# Make the parsers package importable without installing it
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from data.raw_sources.srd_5_2.parsers.base import (
    clean_text,
    slugify,
    parse_cost,
    parse_dice,
    extract_section,
    extract_full_text,
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

    def test_replaces_unicode_minus_sign(self):
        # U+2212 MINUS SIGN appears in PDF ability score modifiers like "−8"
        assert clean_text("−8") == "-8"


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
        assert parse_cost("10 GP") == {"amount": 10.0, "unit": "gp"}

    def test_silver(self):
        assert parse_cost("50 SP") == {"amount": 50.0, "unit": "sp"}

    def test_copper(self):
        assert parse_cost("2 CP") == {"amount": 2.0, "unit": "cp"}

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

    def test_with_unicode_minus_bonus(self):
        # PDF ability modifiers use U+2212 MINUS SIGN, not ASCII hyphen-minus
        assert parse_dice("1d8−1") == {"count": 1, "die": 8, "bonus": -1}

    def test_with_uppercase_d(self):
        assert parse_dice("2D6") == {"count": 2, "die": 6, "bonus": 0}
        assert parse_dice("1D8+2") == {"count": 1, "die": 8, "bonus": 2}


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


class TestExtractFullText:
    def test_injects_table_row_sentinels(self):
        fake_page = MagicMock()
        fake_page.extract_text.return_value = "page text"
        fake_page.extract_tables.return_value = [[["27", "14", "25"]]]
        with patch("pdfplumber.open") as mock_open:
            mock_open.return_value.__enter__.return_value.pages = [fake_page]
            result = extract_full_text("dummy.pdf")
        assert "§TABLE_ROW§27|14|25§" in result
        assert "page text" in result

    def test_skips_empty_table_rows(self):
        fake_page = MagicMock()
        fake_page.extract_text.return_value = "text"
        fake_page.extract_tables.return_value = [[[None, None, None]]]
        with patch("pdfplumber.open") as mock_open:
            mock_open.return_value.__enter__.return_value.pages = [fake_page]
            result = extract_full_text("dummy.pdf")
        assert "§TABLE_ROW§" not in result


from data.raw_sources.srd_5_2.parsers.spells import extract_spells, SpellRecord

# This sample mirrors actual pdfplumber column-extracted text format.
# Level format is "Level N School (Classes)" or "School Cantrip (Classes)"
# Casting Time field is "Action" not "1 action"
SAMPLE_SPELL_TEXT = """\
Spell Descriptions

Acid Arrow
Level 2 Evocation (Wizard)
Casting Time: Action
Range: 90 feet
Components: V, S, M (powdered rhubarb leaf and an adder's stomach)
Duration: Instantaneous
A shimmering green arrow streaks toward a target within range.
At Higher Levels. When you cast this spell using a spell slot of 3rd
level or higher, you deal additional acid damage.

Aid
Level 2 Abjuration (Cleric, Druid, Paladin, Ranger)
Casting Time: Action
Range: 30 feet
Components: V, S, M (a tiny strip of white cloth)
Duration: 8 hours (concentration)
Your spell bolsters your allies with toughness and resolve.

Alarm
Level 1 Abjuration (Ranger, Wizard)
Ritual
Casting Time: 1 minute
Range: 30 feet
Components: V, S, M (a tiny bell and a piece of fine silver wire)
Duration: 8 hours
You set an alarm against unwanted intrusion.

Appendix A: Conditions
"""


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

    def test_cantrip_level_is_zero(self):
        # Cantrips don't appear in the sample but test the level parser
        from data.raw_sources.srd_5_2.parsers.spells import _parse_level
        assert _parse_level("Evocation Cantrip (Wizard)") == 0

    def test_spell_school(self):
        spells = {s.name: s for s in extract_spells(SAMPLE_SPELL_TEXT)}
        assert spells["Acid Arrow"].school == "evocation"

    def test_spell_casting_time(self):
        spells = {s.name: s for s in extract_spells(SAMPLE_SPELL_TEXT)}
        assert spells["Acid Arrow"].casting_time == "Action"

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

    def test_spell_ritual(self):
        spells = {s.name: s for s in extract_spells(SAMPLE_SPELL_TEXT)}
        assert spells["Alarm"].ritual is True
        assert spells["Acid Arrow"].ritual is False

    def test_higher_level_extracted(self):
        spells = {s.name: s for s in extract_spells(SAMPLE_SPELL_TEXT)}
        assert spells["Acid Arrow"].higher_level is not None
        assert "3rd" in spells["Acid Arrow"].higher_level

    def test_sanity_check_raises_on_empty(self):
        with pytest.raises(ValueError, match="fewer than 300"):
            extract_spells("no spells here")
