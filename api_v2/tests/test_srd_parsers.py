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
