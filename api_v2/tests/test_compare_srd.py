"""Tests for the compare_srd management command diff logic."""
import pytest
from api_v2.management.commands.compare_srd import (
    compare_records,
    compare_magic_item_enchantments,
    _normalize,
    _values_equal,
    _db_enchantment_slug,
    _normalize_desc,
    _descriptions_similar,
    FieldMismatch,
    ComparisonResult,
)
from data.raw_sources.srd_5_2.parsers.spells import SpellRecord
from data.raw_sources.srd_5_2.parsers.items import MagicItemRecord
from data.raw_sources.srd_5_2.parsers.classes import ClassRecord
from data.raw_sources.srd_5_2.parsers.origins import FeatRecord, SpeciesRecord


def _make_magic_item(name, enchantment_name=None, rarity="uncommon", requires_attunement=False):
    return MagicItemRecord(
        name=name,
        enchantment_name=enchantment_name if enchantment_name is not None else name,
        rarity=rarity,
        requires_attunement=requires_attunement,
    )


def _make_spell(name, level=1, school="evocation"):
    return SpellRecord(
        name=name, level=level, school=school,
        casting_time="Action", range_text="60 feet",
        verbal=True, somatic=True, material=False,
        material_specified=None, duration="Instantaneous",
        concentration=False, ritual=False, higher_level=None,
    )


SKIP = {"higher_level", "material_specified"}


class TestCompareRecords:
    def test_matching_records_no_mismatches(self):
        pdf = [_make_spell("Fireball", level=3)]
        db = [{"name": "Fireball", "level": 3, "school__name": "evocation",
               "casting_time": "Action", "range_text": "60 feet",
               "verbal": True, "somatic": True, "material": False,
               "duration": "Instantaneous", "concentration": False, "ritual": False}]
        result = compare_records("spells", pdf, db, skip_fields=SKIP)
        assert result.missing == []
        assert result.extra == []
        assert result.mismatches == []

    def test_detects_missing_in_db(self):
        pdf = [_make_spell("Fireball"), _make_spell("Acid Arrow")]
        db = [{"name": "Fireball", "level": 1, "school__name": "evocation",
               "casting_time": "Action", "range_text": "60 feet",
               "verbal": True, "somatic": True, "material": False,
               "duration": "Instantaneous", "concentration": False, "ritual": False}]
        result = compare_records("spells", pdf, db, skip_fields=SKIP)
        assert "Acid Arrow" in result.missing

    def test_detects_extra_in_db(self):
        pdf = [_make_spell("Fireball")]
        db = [
            {"name": "Fireball", "level": 1, "school__name": "evocation",
             "casting_time": "Action", "range_text": "60 feet",
             "verbal": True, "somatic": True, "material": False,
             "duration": "Instantaneous", "concentration": False, "ritual": False},
            {"name": "Bonus Spell", "level": 1, "school__name": "evocation",
             "casting_time": "Action", "range_text": "60 feet",
             "verbal": True, "somatic": True, "material": False,
             "duration": "Instantaneous", "concentration": False, "ritual": False},
        ]
        result = compare_records("spells", pdf, db, skip_fields=SKIP)
        assert "Bonus Spell" in result.extra

    def test_detects_field_mismatch(self):
        pdf = [_make_spell("Fireball", level=3)]
        db = [{"name": "Fireball", "level": 9, "school__name": "evocation",
               "casting_time": "Action", "range_text": "60 feet",
               "verbal": True, "somatic": True, "material": False,
               "duration": "Instantaneous", "concentration": False, "ritual": False}]
        result = compare_records("spells", pdf, db, skip_fields=SKIP)
        assert any(m.field == "level" and m.pdf_value == 3 and m.db_value == 9
                   for m in result.mismatches)

    def test_skip_fields_excluded(self):
        pdf = [_make_spell("Fireball")]
        db = [{"name": "Fireball", "level": 1, "school__name": "evocation",
               "casting_time": "Action", "range_text": "60 feet",
               "verbal": True, "somatic": True, "material": False,
               "duration": "COMPLETELY DIFFERENT",
               "concentration": False, "ritual": False}]
        result = compare_records("spells", pdf, db,
                                 skip_fields={"duration"} | SKIP)
        assert result.mismatches == []

    def test_case_insensitive_string_comparison(self):
        pdf = [_make_spell("Fireball", school="evocation")]
        db = [{"name": "Fireball", "level": 1, "school__name": "Evocation",
               "casting_time": "Action", "range_text": "60 feet",
               "verbal": True, "somatic": True, "material": False,
               "duration": "Instantaneous", "concentration": False, "ritual": False}]
        result = compare_records("spells", pdf, db, skip_fields=SKIP)
        assert result.mismatches == []

    def test_pdf_and_db_counts(self):
        pdf = [_make_spell("Fireball"), _make_spell("Acid Arrow")]
        db = [
            {"name": "Fireball", "level": 1, "school__name": "evocation",
             "casting_time": "Action", "range_text": "60 feet",
             "verbal": True, "somatic": True, "material": False,
             "duration": "Instantaneous", "concentration": False, "ritual": False},
            {"name": "Acid Arrow", "level": 2, "school__name": "evocation",
             "casting_time": "Action", "range_text": "90 feet",
             "verbal": True, "somatic": True, "material": True,
             "duration": "Instantaneous", "concentration": False, "ritual": False},
            {"name": "Extra Spell", "level": 1, "school__name": "evocation",
             "casting_time": "Action", "range_text": "60 feet",
             "verbal": True, "somatic": True, "material": False,
             "duration": "Instantaneous", "concentration": False, "ritual": False},
        ]
        result = compare_records("spells", pdf, db, skip_fields=SKIP)
        assert result.pdf_count == 2
        assert result.db_count == 3

    def test_duration_plural_normalised(self):
        """PDF '8 hours' should match DB '8 hour' after normalisation."""
        assert _normalize("8 hours") == _normalize("8 hour")
        assert _normalize("24 hours") == _normalize("24 hour")
        assert _normalize("10 minutes") == _normalize("10 minute")
        assert _normalize("7 days") == _normalize("7 day")
        assert _normalize("6 rounds") == _normalize("6 round")

    def test_concentration_prefix_stripped(self):
        """PDF 'Concentration, up to 1 minute' should match DB '1 minute'."""
        assert _normalize("Concentration, up to 1 minute") == _normalize("1 minute")
        assert _normalize("Concentration up to 10 minutes") == _normalize("10 minute")
        assert _normalize("Up to 1 hour") == _normalize("1 hour")

    def test_duration_mismatch_no_longer_flagged(self):
        """Spells where PDF has 'Concentration, up to X' and DB has 'X' are equal."""
        pdf = [_make_spell("Bane", level=1)]
        pdf[0] = pdf[0].__class__(
            **{**pdf[0].__dict__,
               "duration": "Concentration, up to 1 minute",
               "concentration": True}
        )
        db = [{"name": "Bane", "level": 1, "school__name": "evocation",
               "casting_time": "Action", "range_text": "60 feet",
               "verbal": True, "somatic": True, "material": False,
               "duration": "1 minute", "concentration": True, "ritual": False}]
        result = compare_records("spells", pdf, db, skip_fields=SKIP)
        assert not any(m.field == "duration" for m in result.mismatches)

    def test_casting_time_count_stripped(self):
        """PDF '1 minute' / '10 minutes' should match DB 'minute' for casting_time."""
        assert _values_equal("1 minute", "minute", field="casting_time")
        assert _values_equal("10 minutes", "minute", field="casting_time")
        assert _values_equal("1 hour", "hour", field="casting_time")
        assert _values_equal("8 hours", "hour", field="casting_time")
        assert _values_equal("24 hours", "hour", field="casting_time")
        assert _values_equal("12 hours", "hour", field="casting_time")

    def test_casting_time_count_not_stripped_for_duration(self):
        """'1 minute' and 'minute' must NOT be equal for non-casting_time fields."""
        assert not _values_equal("1 minute", "minute", field="duration")
        assert not _values_equal("1 hour", "hour", field="duration")

    def test_bonus_action_normalised(self):
        """PDF 'Bonus Action' and line-wrap variant match DB 'bonus-action'."""
        assert _values_equal("Bonus Action", "bonus-action", field="casting_time")
        wrap = "Bonus Action, which you take immedi-"
        assert _values_equal(wrap, "bonus-action", field="casting_time")

    def test_ritual_suffix_stripped(self):
        """PDF 'Action or Ritual' and '1 minute or Ritual' match DB bare value."""
        assert _values_equal("Action or Ritual", "action", field="casting_time")
        assert _values_equal("1 minute or Ritual", "minute", field="casting_time")
        assert _values_equal("1 hour or Ritual", "hour", field="casting_time")

    def test_reaction_description_stripped(self):
        """PDF 'Reaction, which you take when…' matches DB 'reaction'."""
        full = "Reaction, which you take when you are hit by an attack"
        assert _values_equal(full, "reaction", field="casting_time")

    def test_float_comparison_within_tolerance(self):
        """Challenge rating 0.25 vs 0.25000001 should not mismatch."""
        from data.raw_sources.srd_5_2.parsers.creatures import CreatureRecord
        pdf_rec = CreatureRecord(
            name="Goblin", size="Small", type="humanoid", alignment="neutral evil",
            armor_class=15, hit_points=7, hit_dice="2d6",
            walk=30, fly=None, swim=None, burrow=None, climb=None, hover=False,
            strength=8, dexterity=14, constitution=10, intelligence=10, wisdom=8, charisma=8,
            challenge_rating=0.25,
            damage_immunities=(), damage_resistances=(), damage_vulnerabilities=(),
            condition_immunities=(), darkvision_range=60, blindsight_range=0, truesight_range=0,
        )
        pdf = [pdf_rec]
        db = [{"name": "Goblin", "armor_class": 15, "hit_points": 7,
               "ability_score_strength": 8, "ability_score_dexterity": 14,
               "ability_score_constitution": 10, "ability_score_intelligence": 10,
               "ability_score_wisdom": 8, "ability_score_charisma": 8,
               "challenge_rating": 0.25000001,
               "walk": 30, "fly": None, "swim": None, "burrow": None, "climb": None}]
        skip = {
            "hit_dice", "size", "type", "alignment", "hover",
            "damage_immunities", "damage_resistances", "damage_vulnerabilities",
            "condition_immunities", "darkvision_range", "blindsight_range", "truesight_range",
        }
        result = compare_records("creatures", pdf, db, skip_fields=skip)
        assert result.mismatches == []


class TestDbEnchantmentSlug:
    def test_bonus_weapon_maps_to_weapon(self):
        """[WeaponType] (+X) entries map to the PDF enchantment category 'weapon'."""
        assert _db_enchantment_slug("Battleaxe (+1)") == "weapon"
        assert _db_enchantment_slug("Longsword (+3)") == "weapon"
        assert _db_enchantment_slug("Light Hammer (+2)") == "weapon"

    def test_bonus_armor_maps_to_armor(self):
        """[ArmorType] (+X) entries map to the PDF enchantment category 'armor'."""
        assert _db_enchantment_slug("Breastplate (+1)") == "armor"
        assert _db_enchantment_slug("Chain Mail (+2)") == "armor"
        assert _db_enchantment_slug("Plate Armor (+3)") == "armor"

    def test_bonus_shield_maps_to_shield(self):
        assert _db_enchantment_slug("Shield (+1)") == "shield"

    def test_bonus_ammunition_maps_to_ammunition(self):
        assert _db_enchantment_slug("Ammunition (+1)") == "ammunition"

    def test_strips_parenthetical(self):
        assert _db_enchantment_slug("Adamantine Armor (Breastplate)") == "adamantine-armor"
        assert _db_enchantment_slug("Armor of Resistance (Chain Mail)") == "armor-of-resistance"

    def test_strips_weapon_type_suffix(self):
        assert _db_enchantment_slug("Flame Tongue Longsword") == "flame-tongue"
        assert _db_enchantment_slug("Vicious Battleaxe") == "vicious"
        assert _db_enchantment_slug("Weapon of Warning Battleaxe") == "weapon-of-warning"

    def test_strips_two_word_weapon_suffix(self):
        """Two-word weapon type suffixes (e.g. War Pick, Light Hammer) are stripped."""
        assert _db_enchantment_slug("Vicious War Pick") == "vicious"
        assert _db_enchantment_slug("Flame Tongue War Pick") == "flame-tongue"
        assert _db_enchantment_slug("Vicious Light Hammer") == "vicious"
        assert _db_enchantment_slug("Flame Tongue Light Hammer") == "flame-tongue"
        assert _db_enchantment_slug("Vicious Heavy Crossbow") == "vicious"
        assert _db_enchantment_slug("Vicious Hand Crossbow") == "vicious"

    def test_strips_mace_and_sling(self):
        """'mace' and 'sling' are single-word suffixes stripped from enchantment names."""
        assert _db_enchantment_slug("Vicious Mace") == "vicious"
        assert _db_enchantment_slug("Vicious Sling") == "vicious"
        assert _db_enchantment_slug("Flame Tongue Mace") == "flame-tongue"

    def test_strips_armor_type_suffix(self):
        assert _db_enchantment_slug("Elven Chain Mail") == "elven-chain"
        assert _db_enchantment_slug("Demon Breastplate") == "demon"

    def test_unique_item_unchanged(self):
        assert _db_enchantment_slug("Bag of Holding") == "bag-of-holding"
        assert _db_enchantment_slug("Ring of Protection") == "ring-of-protection"

    def test_bonus_space_suffix_stripped(self):
        """'[Name] +N' (space-delimited, no parens) strips the bonus suffix."""
        assert _db_enchantment_slug("Wand of the War Mage +1") == "wand-of-the-war-mage"
        assert _db_enchantment_slug("Wand of the War Mage +2") == "wand-of-the-war-mage"
        assert _db_enchantment_slug("Wand of the War Mage +3") == "wand-of-the-war-mage"

    def test_ammunition_slaying_normalised(self):
        """'Ammunition of [CreatureType] Slaying' normalises to 'ammunition-of-slaying'."""
        assert _db_enchantment_slug("Ammunition of Beast Slaying") == "ammunition-of-slaying"
        assert _db_enchantment_slug("Ammunition of Dragon Slaying") == "ammunition-of-slaying"
        assert _db_enchantment_slug("Ammunition of Undead Slaying") == "ammunition-of-slaying"

    def test_sword_type_prefix_normalised(self):
        """'[sword-expandable weapon] of X' normalises to 'sword-of-X' for known enchantments."""
        assert _db_enchantment_slug("Longsword of Sharpness") == "sword-of-sharpness"
        assert _db_enchantment_slug("Greatsword of Life Stealing") == "sword-of-life-stealing"
        assert _db_enchantment_slug("Glaive of Wounding") == "sword-of-wounding"
        assert _db_enchantment_slug("Rapier of Life Stealing") == "sword-of-life-stealing"
        assert _db_enchantment_slug("Scimitar of Sharpness") == "sword-of-sharpness"
        assert _db_enchantment_slug("Shortsword of Wounding") == "sword-of-wounding"
        # Named items that happen to start with a sword type are NOT normalised
        assert _db_enchantment_slug("Scimitar of Speed") == "scimitar-of-speed"


class TestCompareMagicItemEnchantments:
    SKIP = {"desc"}

    def _db(self, name, rarity="uncommon", requires_attunement=False):
        return {"name": name, "rarity__name": rarity, "requires_attunement": requires_attunement}

    def test_unique_item_exact_match(self):
        pdf = [_make_magic_item("Bag of Holding", rarity="uncommon")]
        db = [self._db("Bag of Holding", rarity="uncommon")]
        result = compare_magic_item_enchantments(pdf, db, self.SKIP)
        assert result.missing == []
        assert result.extra == []
        assert result.mismatches == []

    def test_parenthetical_variant_matches_pdf_enchantment(self):
        """PDF 'Adamantine Armor' should match DB 'Adamantine Armor (Breastplate)' etc."""
        pdf = [_make_magic_item("Adamantine Armor", rarity="uncommon")]
        db = [
            self._db("Adamantine Armor (Breastplate)", rarity="uncommon"),
            self._db("Adamantine Armor (Chain Mail)", rarity="uncommon"),
        ]
        result = compare_magic_item_enchantments(pdf, db, self.SKIP)
        assert result.missing == []
        assert result.extra == []

    def test_weapon_type_suffix_variant_matches(self):
        """DB 'Flame Tongue Longsword' should match PDF 'Flame Tongue'."""
        pdf = [_make_magic_item("Flame Tongue", rarity="rare")]
        db = [
            self._db("Flame Tongue Longsword", rarity="rare"),
            self._db("Flame Tongue Greatsword", rarity="rare"),
        ]
        result = compare_magic_item_enchantments(pdf, db, self.SKIP)
        assert result.missing == []
        assert result.extra == []

    def test_generic_category_suffix_in_pdf_name(self):
        """PDF 'Berserker Axe' matches DB 'Berserker Battleaxe' etc. via generic-suffix rule."""
        pdf = [_make_magic_item("Berserker Axe", enchantment_name="Berserker Axe", rarity="rare")]
        db = [
            self._db("Berserker Battleaxe", rarity="rare"),
            self._db("Berserker Greataxe", rarity="rare"),
        ]
        result = compare_magic_item_enchantments(pdf, db, self.SKIP)
        assert result.missing == []
        assert result.extra == []

    def test_bonus_variant_enchantment_name_matches(self):
        """PDF 'Ammunition, +1, +2, or +3' (enchantment_name='Ammunition') matches DB variants."""
        pdf = [_make_magic_item("Ammunition, +1, +2, or +3",
                                enchantment_name="Ammunition", rarity="uncommon")]
        db = [
            self._db("Ammunition (+1)", rarity="uncommon"),
            self._db("Ammunition (+2)", rarity="rare"),
            self._db("Ammunition (+3)", rarity="very rare"),
        ]
        result = compare_magic_item_enchantments(pdf, db, self.SKIP)
        assert result.missing == []
        assert result.extra == []

    def test_missing_enchantment_reported(self):
        pdf = [_make_magic_item("Ring of Telekinesis", rarity="very rare")]
        db = [self._db("Bag of Holding", rarity="uncommon")]
        result = compare_magic_item_enchantments(pdf, db, self.SKIP)
        assert "Ring of Telekinesis" in result.missing
        assert "Bag of Holding" in result.extra

    def test_rarity_mismatch_detected(self):
        pdf = [_make_magic_item("Bag of Holding", rarity="rare")]
        db = [self._db("Bag of Holding", rarity="uncommon")]
        result = compare_magic_item_enchantments(pdf, db, self.SKIP)
        assert any(m.field == "rarity" for m in result.mismatches)

    def test_pdf_parenthetical_in_enchantment_name_stripped(self):
        """PDF 'Stone of Good Luck (Luckstone)' matches DB 'Stone of Good Luck'."""
        pdf = [_make_magic_item("Stone of Good Luck (Luckstone)", rarity="uncommon")]
        db = [self._db("Stone of Good Luck", rarity="uncommon")]
        result = compare_magic_item_enchantments(pdf, db, self.SKIP)
        assert result.missing == []
        assert result.extra == []

    def test_wand_bonus_space_suffix_matches(self):
        """PDF 'Wand of the War Mage' matches DB 'Wand of the War Mage +1/+2/+3'."""
        pdf = [_make_magic_item("Wand of the War Mage", rarity="uncommon")]
        db = [
            self._db("Wand of the War Mage +1", rarity="uncommon"),
            self._db("Wand of the War Mage +2", rarity="rare"),
            self._db("Wand of the War Mage +3", rarity="very rare"),
        ]
        result = compare_magic_item_enchantments(pdf, db, self.SKIP)
        assert result.missing == []
        assert result.extra == []

    def test_ammunition_slaying_matches_creature_type_variants(self):
        """PDF 'Ammunition of Slaying' matches DB's creature-type-specific variants."""
        pdf = [_make_magic_item("Ammunition of Slaying", rarity="very rare")]
        db = [
            self._db("Ammunition of Beast Slaying", rarity="very rare"),
            self._db("Ammunition of Dragon Slaying", rarity="very rare"),
            self._db("Ammunition of Undead Slaying", rarity="very rare"),
        ]
        result = compare_magic_item_enchantments(pdf, db, self.SKIP)
        assert result.missing == []
        assert result.extra == []

    def test_sword_enchantment_matches_weapon_type_variants(self):
        """PDF 'Sword of Sharpness' matches DB specific weapon type variants."""
        pdf = [_make_magic_item("Sword of Sharpness", rarity="very rare")]
        db = [
            self._db("Longsword of Sharpness", rarity="very rare"),
            self._db("Greatsword of Sharpness", rarity="very rare"),
            self._db("Scimitar of Sharpness", rarity="very rare"),
            self._db("Glaive of Sharpness", rarity="very rare"),
        ]
        result = compare_magic_item_enchantments(pdf, db, self.SKIP)
        assert result.missing == []
        assert result.extra == []

    def test_two_word_weapon_suffix_variants_match(self):
        """DB 'Vicious War Pick', 'Vicious Light Hammer' etc. match PDF 'Vicious'."""
        pdf = [_make_magic_item("Vicious", rarity="rare")]
        db = [
            self._db("Vicious War Pick", rarity="rare"),
            self._db("Vicious Light Hammer", rarity="rare"),
            self._db("Vicious Heavy Crossbow", rarity="rare"),
            self._db("Vicious Mace", rarity="rare"),
            self._db("Vicious Sling", rarity="rare"),
        ]
        result = compare_magic_item_enchantments(pdf, db, self.SKIP)
        assert result.missing == []
        assert result.extra == []


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


class TestDescriptionComparison:
    def test_normalize_desc_removes_line_break_hyphen(self):
        """PDF line-break hyphenation ('concentra-\\ntion') is joined."""
        assert _normalize_desc("concentra-\ntion") == "concentration"
        assert _normalize_desc("non-\nmagical") == "nonmagical"

    def test_normalize_desc_lowercases(self):
        assert _normalize_desc("Fireball") == "fireball"

    def test_normalize_desc_empty(self):
        assert _normalize_desc("") == ""
        assert _normalize_desc(None) == ""  # type: ignore[arg-type]

    def test_descriptions_similar_both_empty(self):
        assert _descriptions_similar("", "") is True

    def test_descriptions_similar_identical(self):
        text = "You set an alarm against intrusion."
        assert _descriptions_similar(text, text) is True

    def test_descriptions_similar_high_overlap(self):
        """Minor formatting differences don't trigger a mismatch."""
        a = "You create a shimmering hand of magical energy in an unoccupied space."
        b = "You create a shimmering hand of magical energy in an unoccupied space!"
        assert _descriptions_similar(a, b) is True

    def test_descriptions_similar_db_empty_pdf_substantial(self):
        """Non-empty PDF description vs empty DB description is a mismatch."""
        pdf = "You set an alarm against intrusion. Choose a door, a window, or an area."
        assert _descriptions_similar(pdf, "") is False

    def test_descriptions_similar_both_short_stubs(self):
        """Both sides having very short content counts as matching (both absent)."""
        assert _descriptions_similar("stub", "stub") is True

    def test_descriptions_similar_significant_truncation(self):
        """DB description that is significantly shorter than PDF is a mismatch."""
        pdf = "A " + "word " * 60  # ~300 chars
        db = "A " + "word " * 20   # ~100 chars — similar start, truncated
        # Ratio will be well below 0.70 due to length difference
        assert _descriptions_similar(pdf, db) is False

    def test_spell_desc_comparison_uses_similarity(self):
        """compare_records uses _descriptions_similar for the 'desc' field."""
        pdf = [_make_spell("Fireball", level=3)]
        pdf[0] = pdf[0].__class__(
            **{**pdf[0].__dict__, "desc": "A bright streak flashes to a point."}
        )
        db = [{"name": "Fireball", "level": 3, "school__name": "evocation",
               "casting_time": "Action", "range_text": "60 feet",
               "verbal": True, "somatic": True, "material": False,
               "duration": "Instantaneous", "concentration": False, "ritual": False,
               "desc": "A bright streak flashes to a point."}]
        result = compare_records("spells", pdf, db, skip_fields={"higher_level", "material_specified"})
        assert not any(m.field == "desc" for m in result.mismatches)
