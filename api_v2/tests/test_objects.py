import requests

from approvaltests import verify_as_json, Options,  DiffReporter
from typing import Callable

API_BASE = f"http://localhost:8000"

class TestObjects:

    def _verify(self, endpoint: str, transformer: Callable[[dict], None] = None):
        response = requests.get(API_BASE + endpoint, allow_redirects=True, headers = {'Accept': 'application/json'}).json()
        if transformer:
            transformer(response)
        verify_as_json(response, options=Options().with_reporter(DiffReporter()))

    # /ITEMS ENDPOINT
    def test_item_example(self):
        path="/v2/items/srd_apparatus-of-the-crab/"
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
        path="/v2/documents/srd/"
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

    # /ARMOR ENDPOINT
    def test_armor_example(self):
        path="/v2/armor/srd_splint/"
        self._verify(path)

    # /GAMESYSTEM ENDPOINT
    def test_gamesystem_example(self):
        path="/v2/rulesets/o5e/"
        self._verify(path)

    # /BACKGROUNDS ENDPOINT
    def test_background_example(self):
        path="/v2/backgrounds/srd_acolyte/"
        self._verify(path)

    # /FEATS ENDPOINT
    def test_feats_example(self):
        path="/v2/feats/srd_grappler/"
        self._verify(path)

    # /RACES ENDPOINT
    def test_races_example(self):
        path="/v2/races/srd_halfling/"
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