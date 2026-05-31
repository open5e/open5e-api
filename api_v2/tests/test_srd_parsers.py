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


from data.raw_sources.srd_5_2.parsers.spells import (
    extract_spells, SpellRecord, extract_spells_from_pdf,
    _extract_column_chars_as_blocks,
)

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
        with pytest.raises(ValueError, match="found no spells"):
            extract_spells("no spells here")

    def test_field_value_not_captured_across_newline(self):
        """_FIELD_RE must not swallow a newline and grab the next label as a value.

        Old regex used r'\\s*' which matched '\\n', so 'Casting Time:\\nRange:\\n'
        produced casting_time='Range:' instead of no match.
        """
        from data.raw_sources.srd_5_2.parsers.spells import _parse_compact_fields
        # Mirrors the font-separated block the PDF extractor produces for Chill Touch:
        # label-only lines (Cambria-Bold) interleaved with value lines (Cambria regular).
        # "Action" appears before "Duration:" because it was separated at the same y.
        block = (
            "ChillTouch\n"
            "Necromancy Cantrip (Wizard)\n"
            "Casting Time:\n"
            "Range:\n"
            "Components:\n"
            "Action\n"       # CT value appears between Components: and Duration:
            "Duration:\n"
            "Touch\n"        # Range value follows Duration: label
            "V, S\n"
            "Instantaneous\n"
            "Body text here.\n"
        )
        fields = _parse_compact_fields(block)
        assert fields.get("Casting Time") == "Action"
        assert fields.get("Range") == "Touch"
        assert fields.get("Components") == "V, S"
        assert fields.get("Duration") == "Instantaneous"

    def test_compact_stats_format_parses_correctly(self):
        """Compact two-column stats (Chill Touch style) parsed via queue fallback."""
        # Mirrors actual font-separated block: label-only lines interleaved with values.
        text = """\
Spell Descriptions

ChillTouch
Necromancy Cantrip (Sorcerer, Warlock, Wizard)
Casting Time:
Range:
Components:
Action
Duration:
Touch
V, S
Instantaneous
Channeling the chill of the grave, make a melee spell attack.
"""
        spells = {s.name: s for s in extract_spells(text)}
        assert "ChillTouch" in spells
        ct = spells["ChillTouch"]
        assert ct.casting_time == "Action"
        assert ct.range_text == "Touch"
        assert ct.verbal is True
        assert ct.somatic is True
        assert ct.material is False
        assert ct.duration == "Instantaneous"

    def test_component_singular_parsed_as_components(self):
        """PDF typo 'Component:' (no trailing s) is accepted and parsed correctly."""
        text = """\
Spell Descriptions

Barkskin
Level 2 Transmutation (Druid, Ranger)
Casting Time: Bonus Action
Range: Touch
Component: V, S, M (a handful of bark)
Duration: 1 hour
You touch a willing creature.
"""
        spells = {s.name: s for s in extract_spells(text)}
        assert "Barkskin" in spells
        bs = spells["Barkskin"]
        assert bs.verbal is True
        assert bs.somatic is True
        assert bs.material is True
        assert bs.material_specified == "a handful of bark"


class TestExtractSpellsFromPdf:
    def test_raises_when_no_spells_found(self):
        """extract_spells_from_pdf raises ValueError when PDF has no spell section or insufficient spells."""
        fake_page = MagicMock()
        fake_page.extract_text.return_value = "Some text without spell descriptions"
        fake_page.chars = []
        fake_page.width = 600
        fake_page.height = 800
        with patch("pdfplumber.open") as mock_open:
            mock_open.return_value.__enter__.return_value.pages = [fake_page]
            with pytest.raises(ValueError, match="expected ≥300"):
                extract_spells_from_pdf("dummy.pdf")

    def test_calls_pdfplumber_open(self):
        """extract_spells_from_pdf successfully calls pdfplumber and handles pages."""
        fake_page = MagicMock()
        fake_page.extract_text.return_value = "Spell Descriptions\n\nSome content here"
        fake_page.chars = []
        fake_page.width = 600
        fake_page.height = 800

        with patch("pdfplumber.open") as mock_open:
            mock_pdf = MagicMock()
            mock_pdf.pages = [fake_page]
            mock_open.return_value.__enter__.return_value = mock_pdf

            # This should call pdfplumber.open and iterate pages
            with pytest.raises(ValueError, match="expected ≥300"):
                extract_spells_from_pdf("dummy.pdf")

            # Verify pdfplumber.open was called with the right path
            mock_open.assert_called_once_with("dummy.pdf")


def _name_chars(text: str, top: float, x0_start: float = 50.0) -> list[dict]:
    """Fake pdfplumber chars for a spell name (GillSans-SemiBold size=12)."""
    return [
        {"fontname": "GillSans-SemiBold", "size": 12.0, "text": ch,
         "x0": x0_start + i * 8, "top": top}
        for i, ch in enumerate(text)
    ]


def _body_chars(text: str, top: float, x0_start: float = 50.0) -> list[dict]:
    """Fake pdfplumber chars for body/field text (Cambria size=10)."""
    return [
        {"fontname": "Cambria", "size": 10.0, "text": ch,
         "x0": x0_start + i * 6, "top": top}
        for i, ch in enumerate(text)
    ]


def _fake_page(chars: list[dict], width: float = 600.0) -> MagicMock:
    page = MagicMock()
    page.width = width
    page.chars = chars
    return page


class TestExtractColumnContinuation:
    """Tests for page-break continuation detection in _extract_column_chars_as_blocks."""

    def test_no_continuation_when_column_starts_with_spell_name(self):
        """first_is_continuation is False when the column opens with a spell name."""
        chars = (
            _name_chars("Fireball", top=100.0) +
            _body_chars("Level 3 Evocation (Wizard)", top=115.0)
        )
        first_is_cont, blocks = _extract_column_chars_as_blocks(
            _fake_page(chars), left_col=True
        )
        assert first_is_cont is False
        assert any("Fireball" in b for b in blocks)

    def test_detects_continuation_when_column_starts_with_body_text(self):
        """first_is_continuation is True when body text precedes the first spell name."""
        chars = (
            _body_chars("Components: V, S, M (a malachite sphere)", top=100.0) +
            _name_chars("AcidSplash", top=200.0) +
            _body_chars("Evocation Cantrip (Wizard)", top=215.0)
        )
        first_is_cont, blocks = _extract_column_chars_as_blocks(
            _fake_page(chars), left_col=True
        )
        assert first_is_cont is True
        assert "Components" in blocks[0]

    def test_entire_column_continuation_when_no_spell_name_found(self):
        """first_is_continuation is True when the column has no spell name at all."""
        chars = (
            _body_chars("Duration: Concentration, up to 1 hour", top=100.0) +
            _body_chars("You create a shimmering field...", top=115.0)
        )
        first_is_cont, blocks = _extract_column_chars_as_blocks(
            _fake_page(chars), left_col=True
        )
        assert first_is_cont is True
        assert len(blocks) == 1

    def test_right_column_same_page_column_break(self):
        """Same-page column break: right column starts with continuation of a left-column spell."""
        # x0_start >= 300 places chars in the right column (page width=600, half=300)
        chars = (
            _body_chars("Components: V, S, M (a piece of bark)", top=100.0, x0_start=310.0) +
            _body_chars("Duration: 1 hour", top=115.0, x0_start=310.0) +
            _name_chars("Blur", top=200.0, x0_start=310.0) +
            _body_chars("Level 2 Illusion (Wizard)", top=215.0, x0_start=310.0)
        )
        first_is_cont, blocks = _extract_column_chars_as_blocks(
            _fake_page(chars), left_col=False
        )
        assert first_is_cont is True
        assert "Components" in blocks[0]
        assert "Blur" in blocks[1]


from data.raw_sources.srd_5_2.parsers.creatures import extract_creatures, CreatureRecord


class TestParseCr:
    def test_integer_cr(self):
        from data.raw_sources.srd_5_2.parsers.creatures import _parse_cr
        assert _parse_cr("21") == 21.0
        assert _parse_cr("4") == 4.0

    def test_fractional_cr(self):
        from data.raw_sources.srd_5_2.parsers.creatures import _parse_cr
        assert _parse_cr("1/4") == pytest.approx(0.25)
        assert _parse_cr("1/2") == pytest.approx(0.5)
        assert _parse_cr("1/8") == pytest.approx(0.125)


# Sample text matching actual pdfplumber extract_text() output format
# Note: AC, HP format is short-form ("AC 17", "HP 21"), not labeled fields
# Note: Ability scores are abbreviated ("Str", "Dex") with modifiers inline
SAMPLE_CREATURE_TEXT = """\
Monsters A-Z

Adult Black Dragon
Huge Dragon (Chromatic), Chaotic Evil
AC 22 Initiative +7 (17) HP 367 (21d12+147)
Speed 40 ft., fly 80 ft., swim 40 ft.
Str 27 +8 +8 Dex 14 +2 +7 Con 25 +7 +12
Int 16 +3 +3 Wis 13 +1 +6 Cha 17 +3 +3
Darkvision 120 ft., Passive Perception 21
Languages Common, Draconic
CR 21 (XP 33,000; PB +7)

Banshee
Medium Undead, Chaotic Evil
AC 12 Initiative +2 (12) HP 58 (13d8)
Speed 0 ft., fly 40 ft. (hover)
Str 1 -5 -5 Dex 14 +2 +2 Con 10 +0 +0
Int 12 +1 +1 Wis 11 +0 +0 Cha 17 +3 +3
Damage Resistances Acid, Fire, Lightning, Thunder; Bludgeoning, Piercing, Slashing
Damage Immunities Cold, Necrotic, Poison
Condition Immunities Charmed, Exhaustion, Frightened, Grappled, Paralyzed
Darkvision 60 ft., Passive Perception 10
Languages Common, Elvish
CR 4 (XP 1,100; PB +2)

Appendix: Conditions
"""


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
        assert creatures["Adult Black Dragon"].armor_class == 22

    def test_creature_hit_points(self):
        creatures = {c.name: c for c in extract_creatures(SAMPLE_CREATURE_TEXT)}
        assert creatures["Adult Black Dragon"].hit_points == 367

    def test_creature_ability_scores(self):
        creatures = {c.name: c for c in extract_creatures(SAMPLE_CREATURE_TEXT)}
        assert creatures["Adult Black Dragon"].strength == 27
        assert creatures["Adult Black Dragon"].dexterity == 14

    def test_creature_challenge_rating(self):
        creatures = {c.name: c for c in extract_creatures(SAMPLE_CREATURE_TEXT)}
        assert creatures["Adult Black Dragon"].challenge_rating == 21.0
        assert creatures["Banshee"].challenge_rating == 4.0

    def test_creature_walk_speed(self):
        creatures = {c.name: c for c in extract_creatures(SAMPLE_CREATURE_TEXT)}
        assert creatures["Adult Black Dragon"].walk == 40
        assert creatures["Adult Black Dragon"].fly == 80
        assert creatures["Adult Black Dragon"].swim == 40

    def test_creature_hover(self):
        creatures = {c.name: c for c in extract_creatures(SAMPLE_CREATURE_TEXT)}
        assert creatures["Banshee"].hover is True
        assert creatures["Adult Black Dragon"].hover is False

    def test_creature_damage_immunities(self):
        creatures = {c.name: c for c in extract_creatures(SAMPLE_CREATURE_TEXT)}
        immunities = [i.lower() for i in creatures["Banshee"].damage_immunities]
        assert "cold" in immunities

    def test_sanity_check_raises_on_empty(self):
        with pytest.raises(ValueError, match="found no creatures"):
            extract_creatures("no creatures here")

    def test_form_only_speed_uses_base_walk(self):
        """Lycanthrope 'X ft. (bear form only)' must not overwrite the base walk speed."""
        text = """\
Monsters A-Z

Werebear
Medium or Small Monstrosity (Lycanthrope), Neutral Good
AC 15 Initiative +0 (10)
HP 135 (18d8 + 54)
Speed 30 ft., 40 ft. (bear form only), Climb 30 ft. (bear form only)
Str 19 +4 +4 Dex 10 +0 +0 Con 17 +3 +3
Int 11 +0 +0 Wis 12 +1 +1 Cha 12 +1 +1
CR 5 (XP 1,800; PB +3)

Appendix
"""
        creatures = {c.name: c for c in extract_creatures(text)}
        werebear = creatures["Werebear"]
        assert werebear.walk == 30
        assert werebear.climb == 30

    def test_unsigned_save_in_compact_ability_row(self):
        """INT/WIS/CHA parsed correctly when the INT save is unsigned in compact format.

        PDF renders 'Int 6-22WIS 11+0+3Cha 12+1+1' when mod=-2 and save=+2 — the
        leading '+' on the save is dropped, producing '-22' which the old greedy
        regex consumed as a single number, causing all three stats to default to 10.
        """
        text = """\
Monsters A-Z

Young White Dragon
Large Dragon (Chromatic), Chaotic Evil
AC 17 Initiative +3 (13)
HP 123 (13d10 + 52)
Speed 40 ft., Burrow 20 ft., Fly 80 ft., Swim 40 ft.
Str 18+4+4Dex 10+0+3Con 18+4+4
Int 6-22WIS 11+0+3Cha 12+1+1
CR 6 (2,300 XP; PB +3)

Appendix
"""
        creatures = {c.name: c for c in extract_creatures(text)}
        dragon = creatures["Young White Dragon"]
        assert dragon.intelligence == 6
        assert dragon.wisdom == 11
        assert dragon.charisma == 12

from data.raw_sources.srd_5_2.parsers.creatures import extract_creatures_from_pdf


class TestExtractCreaturesFromPdf:
    def test_raises_when_no_creatures_found(self):
        """extract_creatures_from_pdf raises ValueError when fewer than 250 creatures parsed."""
        fake_page = MagicMock()
        fake_page.extract_text.return_value = "Some text without monster section"
        fake_page.chars = []
        fake_page.width = 600
        fake_page.height = 800
        with patch("pdfplumber.open") as mock_open:
            mock_open.return_value.__enter__.return_value.pages = [fake_page]
            with pytest.raises(ValueError, match="expected ≥250"):
                extract_creatures_from_pdf("dummy.pdf")

    def test_enters_creature_section_when_detected(self):
        """extract_creatures_from_pdf enters extraction when section heading found."""
        fake_page = MagicMock()
        fake_page.extract_text.return_value = "Monsters A-Z\n\nSome content here"
        fake_page.chars = []  # No chars → no blocks → 0 creatures → raises
        fake_page.width = 600
        fake_page.height = 800
        with patch("pdfplumber.open") as mock_open:
            mock_pdf = MagicMock()
            mock_pdf.pages = [fake_page]
            mock_open.return_value.__enter__.return_value = mock_pdf
            with pytest.raises(ValueError, match="expected ≥250"):
                extract_creatures_from_pdf("dummy.pdf")
            mock_open.assert_called_once_with("dummy.pdf")


from data.raw_sources.srd_5_2.parsers.items import (
    extract_weapons, extract_armor, extract_magic_items,
    extract_weapons_from_pdf, extract_armor_from_pdf, extract_magic_items_from_pdf,
    WeaponRecord, ArmorRecord, MagicItemRecord,
)

# Real PDF format: one weapon per line — Name Damage Properties Mastery Weight Cost
SAMPLE_WEAPON_TEXT = """\
Weapons
Name Damage Properties Mastery Weight Cost
Simple Melee Weapons
Club 1d4 Bludgeoning Light Slow 2 lb. 1 SP
Dagger 1d4 Piercing Finesse, Light, Thrown (Range 20/60) Nick 1 lb. 2 GP
Martial Ranged Weapons
Blowgun 1 Piercing Ammunition (Range 25/100; Needle), Loading Vex 1 lb. 10 GP
Armor
"""

# Real PDF format: Name ACspec StrReq Stealth Weight Cost
SAMPLE_ARMOR_TEXT = """\
Armor
Armor Armor Class (AC) Strength Stealth Weight Cost
Light Armor (1 Minute to Don or Doff)
Leather Armor 11 + Dex modifier — — 10 lb. 10 GP
Medium Armor (5 Minutes to Don and 1 Minute to Doff)
Chain Shirt 13 + Dex modifier (max 2) — — 20 lb. 50 GP
Heavy Armor (10 Minutes to Don and 5 Minutes to Doff)
Chain Mail 16 Str 13 Disadvantage 55 lb. 75 GP
Tools
"""

# Real PDF format: Name line then Type, Rarity (Requires Attunement) line
SAMPLE_MAGIC_ITEM_TEXT = """\
Magic Items A-Z

Bag of Holding
Wondrous Item, Uncommon

Cloak of Protection
Cloak, Uncommon (Requires Attunement)

Vorpal Sword
Weapon (Any Sword That Deals Slashing Damage), Legendary (Requires Attunement)

Spells
"""


class TestExtractWeapons:
    def test_finds_dagger(self):
        weapons = extract_weapons(SAMPLE_WEAPON_TEXT)
        names = [w.name for w in weapons]
        assert "Dagger" in names

    def test_finds_club(self):
        weapons = extract_weapons(SAMPLE_WEAPON_TEXT)
        names = [w.name for w in weapons]
        assert "Club" in names

    def test_weapon_damage_type(self):
        weapons = {w.name: w for w in extract_weapons(SAMPLE_WEAPON_TEXT)}
        assert weapons["Dagger"].damage_type == "piercing"
        assert weapons["Club"].damage_type == "bludgeoning"

    def test_weapon_cost(self):
        weapons = {w.name: w for w in extract_weapons(SAMPLE_WEAPON_TEXT)}
        assert weapons["Dagger"].cost == {"amount": 2.0, "unit": "gp"}
        assert weapons["Club"].cost == {"amount": 1.0, "unit": "sp"}

    def test_weapon_damage_dice(self):
        weapons = {w.name: w for w in extract_weapons(SAMPLE_WEAPON_TEXT)}
        assert weapons["Dagger"].damage == {"count": 1, "die": 4, "bonus": 0}

    def test_blowgun_flat_damage_is_none(self):
        weapons = {w.name: w for w in extract_weapons(SAMPLE_WEAPON_TEXT)}
        assert weapons["Blowgun"].damage is None
        assert weapons["Blowgun"].damage_type == "piercing"

    def test_finds_light_hammer(self):
        # Light Hammer starts with "Light" — must not be skipped by section-header filter
        text = """\
Weapons
Name Damage Properties Mastery Weight Cost
Simple Melee Weapons
Light Hammer 1d4 Bludgeoning Light, Thrown (Range 20/60) Nick 2 lb. 2 GP
Armor
"""
        weapons = extract_weapons(text)
        names = [w.name for w in weapons]
        assert "Light Hammer" in names

    def test_sanity_check_raises_on_empty(self):
        with pytest.raises(ValueError, match="found no weapons"):
            extract_weapons("no weapons here")


class TestExtractArmor:
    def test_finds_leather_armor(self):
        armor = extract_armor(SAMPLE_ARMOR_TEXT)
        names = [a.name for a in armor]
        assert "Leather Armor" in names

    def test_finds_chain_mail(self):
        armor = extract_armor(SAMPLE_ARMOR_TEXT)
        names = [a.name for a in armor]
        assert "Chain Mail" in names

    def test_light_armor_ac(self):
        armor = {a.name: a for a in extract_armor(SAMPLE_ARMOR_TEXT)}
        assert armor["Leather Armor"].ac_base == 11
        assert armor["Leather Armor"].ac_add_dex is True
        assert armor["Leather Armor"].ac_cap_dex is None
        assert armor["Leather Armor"].stealth_disadvantage is False
        assert armor["Leather Armor"].strength_required is None

    def test_medium_armor_with_cap(self):
        armor = {a.name: a for a in extract_armor(SAMPLE_ARMOR_TEXT)}
        assert armor["Chain Shirt"].ac_base == 13
        assert armor["Chain Shirt"].ac_add_dex is True
        assert armor["Chain Shirt"].ac_cap_dex == 2

    def test_heavy_armor_ac(self):
        armor = {a.name: a for a in extract_armor(SAMPLE_ARMOR_TEXT)}
        assert armor["Chain Mail"].ac_base == 16
        assert armor["Chain Mail"].ac_add_dex is False
        assert armor["Chain Mail"].strength_required == 13
        assert armor["Chain Mail"].stealth_disadvantage is True

    def test_sanity_check_raises_on_empty(self):
        with pytest.raises(ValueError, match="found no armor"):
            extract_armor("no armor here")


class TestExtractMagicItems:
    def test_finds_bag_of_holding(self):
        items = extract_magic_items(SAMPLE_MAGIC_ITEM_TEXT)
        names = [i.name for i in items]
        assert "Bag of Holding" in names

    def test_finds_cloak_of_protection(self):
        items = extract_magic_items(SAMPLE_MAGIC_ITEM_TEXT)
        names = [i.name for i in items]
        assert "Cloak of Protection" in names

    def test_magic_item_rarity(self):
        items = {i.name: i for i in extract_magic_items(SAMPLE_MAGIC_ITEM_TEXT)}
        assert items["Bag of Holding"].rarity == "uncommon"
        assert items["Vorpal Sword"].rarity == "legendary"

    def test_magic_item_attunement(self):
        items = {i.name: i for i in extract_magic_items(SAMPLE_MAGIC_ITEM_TEXT)}
        assert items["Bag of Holding"].requires_attunement is False
        assert items["Cloak of Protection"].requires_attunement is True

    def test_multiline_name_not_duplicated(self):
        # "and Location" is a continuation of the previous name — should NOT appear as its own item
        text = """\
Magic Items A-Z

Amulet of Proof against Detection
and Location
Wondrous Item, Uncommon (Requires Attunement)

Spells
"""
        items = extract_magic_items(text)
        names = [i.name for i in items]
        assert "Amulet of Proof against Detection and Location" in names
        assert not any("and Location" == n for n in names)
        assert not any(n.startswith("and ") for n in names)

    def test_sanity_check_raises_on_empty(self):
        with pytest.raises(ValueError, match="found no magic items"):
            extract_magic_items("no items here")

    def test_enchantment_name_unique_item(self):
        """Unique items have enchantment_name == name."""
        items = {i.name: i for i in extract_magic_items(SAMPLE_MAGIC_ITEM_TEXT)}
        assert items["Bag of Holding"].enchantment_name == "Bag of Holding"
        assert items["Vorpal Sword"].enchantment_name == "Vorpal Sword"

    def test_enchantment_name_strips_bonus_variant(self):
        """', +1, +2, or +3' suffix is stripped from enchantment_name."""
        text = """\
Magic Items A-Z

Weapon, +1, +2, or +3
Weapon (Any), Uncommon (+1), Rare (+2), or Very Rare (+3)

Wand of the War Mage, +1, +2, or +3
Wand, Uncommon (+1)

Spells
"""
        items = {i.name: i for i in extract_magic_items(text)}
        assert items["Weapon, +1, +2, or +3"].enchantment_name == "Weapon"
        assert items["Wand of the War Mage, +1, +2, or +3"].enchantment_name == "Wand of the War Mage"


# Minimal weapon text with only 1 weapon (fewer than 30) to trigger ≥30 guard
_FEW_WEAPONS_TEXT = """\
Weapons
Name Damage Properties Mastery Weight Cost
Simple Melee Weapons
Dagger 1d4 Piercing Finesse, Light, Thrown (Range 20/60) Nick 1 lb. 2 GP
Armor
"""

# Minimal armor text with only 1 entry (fewer than 10) to trigger ≥10 guard
_FEW_ARMOR_TEXT = """\
Armor
Armor Armor Class (AC) Strength Stealth Weight Cost
Light Armor (1 Minute to Don or Doff)
Leather Armor 11 + Dex modifier — — 10 lb. 10 GP
Tools
"""


class TestExtractWeaponsFromPdf:
    def test_raises_when_no_weapons_found(self):
        fake_page = MagicMock()
        fake_page.extract_text.return_value = _FEW_WEAPONS_TEXT
        fake_page.extract_tables.return_value = []
        fake_page.chars = []
        fake_page.width = 600
        with patch("pdfplumber.open") as mock_open:
            mock_open.return_value.__enter__.return_value.pages = [fake_page]
            with pytest.raises(ValueError, match="expected ≥30"):
                extract_weapons_from_pdf("dummy.pdf")

    def test_calls_pdfplumber_open(self):
        fake_page = MagicMock()
        fake_page.extract_text.return_value = _FEW_WEAPONS_TEXT
        fake_page.extract_tables.return_value = []
        fake_page.chars = []
        fake_page.width = 600
        with patch("pdfplumber.open") as mock_open:
            mock_open.return_value.__enter__.return_value.pages = [fake_page]
            with pytest.raises(ValueError, match="expected ≥30"):
                extract_weapons_from_pdf("dummy.pdf")
            mock_open.assert_called_once_with("dummy.pdf")


class TestExtractArmorFromPdf:
    def test_raises_when_no_armor_found(self):
        fake_page = MagicMock()
        fake_page.extract_text.return_value = _FEW_ARMOR_TEXT
        fake_page.extract_tables.return_value = []
        fake_page.chars = []
        fake_page.width = 600
        with patch("pdfplumber.open") as mock_open:
            mock_open.return_value.__enter__.return_value.pages = [fake_page]
            with pytest.raises(ValueError, match="expected ≥10"):
                extract_armor_from_pdf("dummy.pdf")

    def test_calls_pdfplumber_open(self):
        fake_page = MagicMock()
        fake_page.extract_text.return_value = _FEW_ARMOR_TEXT
        fake_page.extract_tables.return_value = []
        fake_page.chars = []
        fake_page.width = 600
        with patch("pdfplumber.open") as mock_open:
            mock_open.return_value.__enter__.return_value.pages = [fake_page]
            with pytest.raises(ValueError, match="expected ≥10"):
                extract_armor_from_pdf("dummy.pdf")
            mock_open.assert_called_once_with("dummy.pdf")


class TestExtractMagicItemsFromPdf:
    def test_raises_when_no_magic_items_found(self):
        fake_page = MagicMock()
        fake_page.extract_text.return_value = "Some text without magic items"
        fake_page.chars = []
        fake_page.width = 600
        with patch("pdfplumber.open") as mock_open:
            mock_open.return_value.__enter__.return_value.pages = [fake_page]
            with pytest.raises(ValueError, match="expected ≥200"):
                extract_magic_items_from_pdf("dummy.pdf")

    def test_enters_magic_items_section_when_detected(self):
        """extract_magic_items_from_pdf enters extraction when section heading found."""
        # Provide all chars of "Magic Items" at size 18 so _is_magic_items_section_heading
        # returns True, triggering section entry. No item data → 0 items → raises.
        heading_text = "Magic Items"
        heading_chars = [
            {
                "text": ch,
                "fontname": "GillSans-SemiBold",
                "size": 18.0,
                "x0": float(i * 8),
                "top": 100.0,
            }
            for i, ch in enumerate(heading_text)
        ]
        fake_page = MagicMock()
        fake_page.extract_text.return_value = "Magic Items A-Z"
        fake_page.chars = heading_chars
        fake_page.width = 600
        with patch("pdfplumber.open") as mock_open:
            mock_open.return_value.__enter__.return_value.pages = [fake_page]
            with pytest.raises(ValueError, match="expected ≥200"):
                extract_magic_items_from_pdf("dummy.pdf")
            mock_open.assert_called_once_with("dummy.pdf")


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
    def test_raises_when_no_classes_found(self):
        import pytest
        from unittest.mock import patch, MagicMock
        from data.raw_sources.srd_5_2.parsers.classes import extract_classes_from_pdf
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "No classes here"
        mock_page.page_number = 1
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = lambda s: s
        mock_pdf.__exit__ = MagicMock(return_value=False)
        with patch("pdfplumber.open", return_value=mock_pdf):
            with pytest.raises(ValueError, match="expected ≥10"):
                extract_classes_from_pdf("fake.pdf")


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
        """Build chars for a feat entry matching the real SRD PDF font profile.

        Feat names are GillSans-SemiBold sz=12; type tags are Cambria-Italic sz=10.
        """
        cat_text = category
        if prerequisite:
            cat_text += f" (Prerequisite: {prerequisite})"
        return (
            [(name, "GillSans-SemiBold", 12, x, y_name)]
            + [(cat_text, "Cambria-Italic", 10, x, y_name + 14)]
        )

    def test_extracts_origin_feat(self):
        chars = (
            self._feat_chars("Alert", "Origin Feat", y_name=100)
            + self._feat_chars("Blessed One", "Origin Feat", y_name=130)
            + self._feat_chars("Canny", "Origin Feat", y_name=160)
            + self._feat_chars("Dragonborn", "Origin Feat", y_name=190)
            + self._feat_chars("Fey Touched", "Origin Feat", y_name=220)
        )
        page = self._make_page(chars)
        records = extract_feats([page])
        alert = [r for r in records if r.name == "Alert"][0]
        assert alert.feat_type == "Origin"
        assert alert.prerequisite == ""

    def test_extracts_general_feat_with_prerequisite(self):
        chars = (
            self._feat_chars("Ability Score Improvement", "General Feat", "Level 4+", y_name=100)
            + self._feat_chars("Actor", "General Feat", y_name=130)
            + self._feat_chars("Alert", "General Feat", y_name=160)
            + self._feat_chars("Crafter", "General Feat", y_name=190)
            + self._feat_chars("Diplomat", "General Feat", y_name=220)
        )
        page = self._make_page(chars)
        records = extract_feats([page])
        asi = [r for r in records if r.name == "Ability Score Improvement"][0]
        assert asi.feat_type == "General"
        assert asi.prerequisite == "Level 4+"

    def test_extracts_fighting_style_feat(self):
        chars = (
            self._feat_chars("Archery", "Fighting Style Feat", "Fighting Style Feature", y_name=100)
            + self._feat_chars("Blessed Warrior", "Fighting Style Feat", y_name=130)
            + self._feat_chars("Defense", "Fighting Style Feat", y_name=160)
            + self._feat_chars("Dueling", "Fighting Style Feat", y_name=190)
            + self._feat_chars("Great Weapon Fighting", "Fighting Style Feat", y_name=220)
        )
        page = self._make_page(chars)
        records = extract_feats([page])
        archery = [r for r in records if r.name == "Archery"][0]
        assert archery.feat_type == "Fighting Style"

    def test_extracts_epic_boon_feat(self):
        chars = (
            self._feat_chars("Boon of Combat Prowess", "Epic Boon Feat", "Level 19+", y_name=100)
            + self._feat_chars("Boon of Fortitude", "Epic Boon Feat", y_name=130)
            + self._feat_chars("Boon of High Magic", "Epic Boon Feat", y_name=160)
            + self._feat_chars("Boon of Irresistible Offense", "Epic Boon Feat", y_name=190)
            + self._feat_chars("Boon of Spell Mastery", "Epic Boon Feat", y_name=220)
        )
        page = self._make_page(chars)
        records = extract_feats([page])
        boon = [r for r in records if r.name == "Boon of Combat Prowess"][0]
        assert boon.feat_type == "Epic Boon"

    def test_ignores_section_header_without_tag(self):
        """Group headers like 'Origin Feats' (sz=14 GillSans) are not feat names."""
        chars = (
            [("Origin Feats", "GillSans-SemiBold", 14, 50, 100)]
            + self._feat_chars("Alert", "Origin Feat", y_name=130)
            + self._feat_chars("Blessed One", "Origin Feat", y_name=160)
            + self._feat_chars("Canny", "Origin Feat", y_name=190)
            + self._feat_chars("Dragonborn", "Origin Feat", y_name=220)
            + self._feat_chars("Fey Touched", "Origin Feat", y_name=250)
        )
        page = self._make_page(chars)
        # sz=14 is not the feat-name size (12) → section header is not recognised as a feat
        records = extract_feats([page])
        names = [r.name for r in records]
        assert "Origin Feats" not in names
        assert "Alert" in names

    def test_sanity_check_raises_on_empty(self):
        import pytest
        from unittest.mock import MagicMock
        page = MagicMock()
        page.page_number = 1
        page.width = 600.0
        page.chars = []
        with pytest.raises(ValueError, match="expected ≥5"):
            extract_feats([page])


class TestExtractFeatsFromPdf:
    def test_raises_when_no_feats_found(self):
        import pytest
        from unittest.mock import patch, MagicMock
        from data.raw_sources.srd_5_2.parsers.origins import extract_feats_from_pdf
        mock_page = MagicMock()
        mock_page.page_number = 1
        mock_page.width = 600.0
        mock_page.chars = []
        mock_page.extract_text.return_value = "Feats\nsome content"
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = lambda s: s
        mock_pdf.__exit__ = MagicMock(return_value=False)
        with patch("pdfplumber.open", return_value=mock_pdf):
            with pytest.raises(ValueError, match="expected ≥5"):
                extract_feats_from_pdf("fake.pdf")
