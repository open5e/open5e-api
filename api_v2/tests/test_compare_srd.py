"""Tests for the compare_srd management command diff logic."""
import pytest
from api_v2.management.commands.compare_srd import (
    compare_records,
    FieldMismatch,
    ComparisonResult,
)
from data.raw_sources.srd_5_2.parsers.spells import SpellRecord


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
        result = compare_records("creatures", pdf, db, skip_fields={"hit_dice", "size", "type", "alignment",
                                                                      "damage_immunities", "damage_resistances",
                                                                      "damage_vulnerabilities", "condition_immunities",
                                                                      "darkvision_range", "blindsight_range",
                                                                      "truesight_range", "hover"})
        assert result.mismatches == []
