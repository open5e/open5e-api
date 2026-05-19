import requests

from approvaltests import verify_as_json, Options,  DiffReporter
from typing import Callable

API_BASE = f"http://localhost:8000"


VALID_CASTING_TIME = {
    'reaction', 'bonus-action', 'action', 'turn', 'round',
    '1minute', '5minutes', '10minutes',
    '1hour', '4hours', '7hours', '8hours', '9hours', '12hours', '24hours',
    '1week',
}
VALID_TARGET_TYPE = {'creature', 'object', 'point', 'area'}
VALID_SHAPE_TYPE = {'cone', 'cube', 'cylinder', 'line', 'sphere'}
VALID_DURATION = {
    'instantaneous', 'instantaneous or special',
    '1 turn', '1 round', 'concentration + 1 round',
    '2 rounds', '3 rounds', '4 rounds', '1d4+2 rounds', '5 rounds', '6 rounds', '10 rounds',
    'up to 1 minute', '1 minute', '1 minute, or until expended', '1 minute, until expended',
    '5 minutes', '10 minutes', '1 minute or 1 hour',
    'up to 1 hour', '1 hour', '1 hour or until triggered',
    '2 hours', '3 hours', '1d10 hours', '6 hours', '2-12 hours', 'up to 8 hours', '8 hours',
    '1 hour/caster level', '10 hours', '12 hours',
    '24 hours or until the target attempts a third death saving throw', '24 hours',
    '1 day', '3 days', '5 days', '7 days', '10 days', '13 days', '30 days',
    '1 year', 'special',
    'until dispelled or destroyed', 'until destroyed', 'until dispelled',
    'until cured or dispelled', 'until dispelled or triggered',
    'permanent until discharged', 'permanent; one generation', 'permanent',
}


def _fetch_all_spells():
    spells = []
    url = f"{API_BASE}/v2/spells/?limit=500"
    while url:
        data = requests.get(url, headers={'Accept': 'application/json'}).json()
        spells.extend(data['results'])
        url = data.get('next')
    return spells


class TestSpellCastingOptions:
    """Tests to validate spell casting options data integrity."""

    def test_all_spells_with_higher_level_have_casting_options(self):
        """Every spell with higher_level text should have at least one casting option."""
        response = requests.get(
            f"{API_BASE}/v2/spells/?limit=1000",
            headers={'Accept': 'application/json'}
        ).json()
        
        spells_missing_options = []
        for spell in response['results']:
            if spell.get('higher_level') and not spell.get('casting_options'):
                spells_missing_options.append(spell['key'])
        
        assert not spells_missing_options, \
            f"Spells with higher_level but no casting_options: {spells_missing_options}"

    def test_no_duplicate_casting_option_types(self):
        """No spell should have duplicate casting option types."""
        response = requests.get(
            f"{API_BASE}/v2/spells/?limit=1000",
            headers={'Accept': 'application/json'}
        ).json()
        
        spells_with_duplicates = []
        for spell in response['results']:
            casting_options = spell.get('casting_options', [])
            types = [opt['type'] for opt in casting_options]
            if len(types) != len(set(types)):
                duplicates = [t for t in types if types.count(t) > 1]
                spells_with_duplicates.append(f"{spell['name']}: {set(duplicates)}")
        
        assert not spells_with_duplicates, \
            f"Spells with duplicate casting option types: {spells_with_duplicates}"

    def test_all_spell_casting_times_are_valid(self):
        """All spells must have a casting_time value that matches the enumerated choices."""
        violations = [
            f"{s['key']}: casting_time={s['casting_time']!r}"
            for s in _fetch_all_spells()
            if s.get('casting_time') not in VALID_CASTING_TIME
        ]
        assert not violations, f"Spells with invalid casting_time: {violations}"

    def test_all_spell_target_types_are_valid(self):
        """All spells with a target_type must use an enumerated choice value."""
        violations = [
            f"{s['key']}: target_type={s['target_type']!r}"
            for s in _fetch_all_spells()
            if s.get('target_type') is not None and s['target_type'] not in VALID_TARGET_TYPE
        ]
        assert not violations, f"Spells with invalid target_type: {violations}"

    def test_all_spell_shape_types_are_valid(self):
        """All spells with a shape_type must use an enumerated choice value."""
        violations = [
            f"{s['key']}: shape_type={s['shape_type']!r}"
            for s in _fetch_all_spells()
            if s.get('shape_type') is not None and s['shape_type'] not in VALID_SHAPE_TYPE
        ]
        assert not violations, f"Spells with invalid shape_type: {violations}"

    def test_all_spell_durations_are_valid(self):
        """All spells must have a duration value that matches the enumerated choices."""
        violations = [
            f"{s['key']}: duration={s['duration']!r}"
            for s in _fetch_all_spells()
            if s.get('duration') not in VALID_DURATION
        ]
        assert not violations, f"Spells with invalid duration: {violations}"


class TestObjects:

    def _verify(self, endpoint: str, transformer: Callable[[dict], None] = None):
        response = requests.get(API_BASE + endpoint, allow_redirects=True, headers = {'Accept': 'application/json'}).json()
        if transformer:
            transformer(response)
        verify_as_json(response, options=Options().with_reporter(DiffReporter()))

    # /ITEMS ENDPOINT
    def test_item_example(self):
        path="/v2/magicitems/srd_apparatus-of-the-crab/"
        self._verify(path)

    def test_item_melee_weapon_example(self):
        path="/v2/items/srd_shortsword/"
        self._verify(path)

    def test_item_ranged_weapon_example(self):
        path="/v2/items/srd_longbow/"
        self._verify(path)

    def test_item_armor_example(self):
        path="/v2/items/srd_splint-armor/"
        self._verify(path)

    # /ITEMSETS ENDPOINT
    def test_item_set_example(self):
        path="/v2/itemsets/arcane-focuses/"
        self._verify(path)

    # /ITEMCATEGORIES ENDPOINT
    def test_item_category_example(self):
        path="/v2/itemcategories/weapon/"
        self._verify(path)

    # /DOCUMENTS ENDPOINT
    def test_document_example(self):
        path="/v2/documents/srd-2014/"
        self._verify(path)

    # /LICENSES ENDPOINT
    def test_license_example(self):
        path="/v2/licenses/ogl-10a/"
        self._verify(path)

    # /PUBLISHERS ENDPOINT
    def test_publisher_example(self):
        path="/v2/publishers/wizards-of-the-coast/"
        self._verify(path)
    
    # /WEAPONS ENDPOINT
    def test_weapon_example(self):
        path="/v2/weapons/srd_shortsword/"
        self._verify(path)

    def test_weapon_with_mastery_example(self):
        path="/v2/weapons/srd-2024_longsword/"
        self._verify(path)

    # /ARMOR ENDPOINT
    def test_armor_example(self):
        path="/v2/armor/srd_splint/"
        self._verify(path)

    # /GAMESYSTEM ENDPOINT
    def test_gamesystem_example(self):
        path="/v2/gamesystems/o5e/"
        self._verify(path)

    # /BACKGROUNDS ENDPOINT
    def test_background_example(self):
        path="/v2/backgrounds/srd_acolyte/"
        self._verify(path)

    # /FEATS ENDPOINT
    def test_feats_example(self):
        path="/v2/feats/srd_grappler/"
        self._verify(path)

    # /SPECIES ENDPOINT
    def test_species_example(self):
        path="/v2/species/srd_halfling/"
        self._verify(path)

    # /CREATURES ENDPOINT
    def test_creature_goblin_example(self):
        path="/v2/creatures/srd_goblin/"
        self._verify(path)

    def test_creature_guard_example(self):
        path="/v2/creatures/srd_guard/"
        self._verify(path)

    def test_creature_ancient_example(self):
        path="/v2/creatures/srd_ancient-red-dragon/"
        self._verify(path)

    # CREATURETYPES ENDPOINT
    def test_creaturetype_example(self):
        path="/v2/creaturetypes/elemental/"
        self._verify(path)

    # CREATURESETS ENDPOINT
    def test_creatureset_example(self):
        path="/v2/creaturesets/common-mounts/"
        self._verify(path)

    # DAMAGETYPES ENDPOINT
    def test_damagetype_example(self):
        path="/v2/damagetypes/radiant/"
        self._verify(path)

    # LANGUAGES ENDPOINT
    def test_language_example(self):
        path="/v2/languages/abyssal/"
        self._verify(path)

    # ALIGNMENTS ENDPOINT
    def test_alignment_example(self):
        path="/v2/alignments/chaotic-good/"
        self._verify(path)

    # CONDITIONS ENDPOINT
    def test_condition_example(self):
        path="/v2/conditions/stunned/"
        self._verify(path)

    # SPELLS ENDPOINT
    def test_spell_cantrip_example(self):
        path="/v2/spells/srd_prestidigitation/"
        self._verify(path)
    
    def test_spell_fireball(self):
        path="/v2/spells/srd_fireball/"
        self._verify(path)
    
    def test_spell_wish(self):
        path="/v2/spells/srd_wish/"
        self._verify(path)
    
    # CLASSES ENDPOINT
    def test_class_example(self):
        path="/v2/classes/srd_barbarian/"
        self._verify(path)
    
    def test_subclass_example(self):
        path="/v2/classes/srd_thief/"
        self._verify(path)
    
    # SIZES ENDPOINT
    def test_size_example(self):
        path="/v2/sizes/huge/"
        self._verify(path)
    
    # ITEMRARITIES ENDPOINT
    def test_itemrarity_example(self):
        path="/v2/itemrarities/common/"
        self._verify(path)

    # ENVIRONMENTS ENDPOINT
    def test_environment_example(self):
        path="/v2/environments/srd_astral-plane/"
        self._verify(path)

    # ABILITIES ENDPOINT
    def test_ability_example(self):
        path="/v2/abilities/dex/"
        self._verify(path)

    # SKILLS ENDPOINT
    def test_skill_example(self):
        path="/v2/skills/insight/"
        self._verify(path)

    # WEAPONPROPERTIES ENDPOINT
    def test_weaponproperty_standard_example(self):
        path="/v2/weaponproperties/srd-2014_finesse-wp/"
        self._verify(path)

    def test_weaponproperty_mastery_example(self):
        path="/v2/weaponproperties/srd-2024_cleave-mastery/"
        self._verify(path)

    def test_weaponproperties_mastery_filter(self):
        path="/v2/weaponproperties/?type=Mastery&limit=3"
        self._verify(path)

    def test_weaponproperties_standard_filter(self):
        path="/v2/weaponproperties/?type__isnull=true&document__key=srd-2024&limit=3"
        self._verify(path)