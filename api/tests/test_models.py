from django.test import TestCase
from api.models import Spell
from api.models import Document

class SpellModelTestCase(TestCase):
    def setUp(self):
        
        self.test_spell=Spell.objects.create(
            name='Test Spell',
            can_be_cast_as_ritual=True,
            requires_concentration=True,
            spell_level=0,
            target_range_sort=10,
            requires_verbal_components=True,
            requires_somatic_components=True,
            requires_material_components=True,
            document=Document.objects.create(title="test", slug="test"))


    def test_ritual(self):
        self.test_spell.can_be_cast_as_ritual= True
        self.assertEqual(self.test_spell.v1_ritual(),'yes')
        self.test_spell.can_be_cast_as_ritual= False
        self.assertEqual(self.test_spell.v1_ritual(),'no')

    def test_concentration(self):
        self.test_spell.requires_concentration=True
        self.assertEqual(self.test_spell.v1_concentration(),'yes')
        self.test_spell.requires_concentration=False
        self.assertEqual(self.test_spell.v1_concentration(),'no')

    def test_spell_level(self):
        self.test_spell.spell_level=0
        self.assertEqual(self.test_spell.v1_level(),"Cantrip")
        
        self.test_spell.spell_level=1
        self.assertEqual(self.test_spell.v1_level(),"1st-level")

        self.test_spell.spell_level=9
        self.assertEqual(self.test_spell.v1_level(),"9th-level")

    def test_spell_components(self):
        self.test_spell.requires_verbal_components=True
        self.test_spell.requires_somatic_components=True
        self.test_spell.requires_material_components=True
        self.assertEqual(self.test_spell.v1_components(),'V, S, M')

        self.test_spell.requires_somatic_components=False
        self.assertEqual(self.test_spell.v1_components(),'V, M')

        self.test_spell.requires_material_components=False
        self.assertEqual(self.test_spell.v1_components(),'V')

        self.test_spell.requires_verbal_components=False
        self.test_spell.requires_somatic_components=True
        self.assertEqual(self.test_spell.v1_components(),'S')