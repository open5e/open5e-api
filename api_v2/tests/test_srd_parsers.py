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


from data.raw_sources.srd_5_2.parsers.spells import extract_spells, SpellRecord, extract_spells_from_pdf

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
        # Build a fake page that has the GillSans-SemiBold size-18 heading char
        # but no actual item data → 0 items → raises
        fake_heading_char = {
            "text": "M",
            "fontname": "GillSans-SemiBold",
            "size": 18.0,
            "x0": 50.0,
            "top": 100.0,
        }
        fake_page = MagicMock()
        fake_page.extract_text.return_value = "Magic Items A-Z"
        fake_page.chars = [fake_heading_char]
        fake_page.width = 600
        with patch("pdfplumber.open") as mock_open:
            mock_open.return_value.__enter__.return_value.pages = [fake_page]
            with pytest.raises(ValueError, match="expected ≥200"):
                extract_magic_items_from_pdf("dummy.pdf")
            mock_open.assert_called_once_with("dummy.pdf")
