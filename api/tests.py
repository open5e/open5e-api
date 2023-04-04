import json

from rest_framework.test import APITestCase

# Create your tests here.

class APIRootTest(APITestCase):
    def test_get_root_headers(self):
        response = self.client.get(f'/?format=json')
        # Assert basic headers
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['allow'],'GET, HEAD, OPTIONS')
        self.assertEqual(response.headers['content-type'],'application/json')
        self.assertEqual(response.headers['X-Frame-Options'],'DENY')
        self.assertEqual(response.headers['X-Content-Type-Options'],'nosniff')
        self.assertEqual(response.headers['Referrer-Policy'],'same-origin')
        
    def test_get_root_list(self):
        response = self.client.get(f'/?format=json')
        # Check the response for each of the known endpoints. Two results, one for the name, one for the link.
        self.assertContains(response,'manifest',count=2)
        self.assertContains(response,'spells',count=2)
        self.assertContains(response,'monsters',count=2)
        self.assertContains(response,'documents',count=2)
        self.assertContains(response,'backgrounds',count=2)
        self.assertContains(response,'planes',count=2)
        self.assertContains(response,'sections',count=2)
        self.assertContains(response,'feats',count=2)
        self.assertContains(response,'conditions',count=2)
        self.assertContains(response,'races',count=2)
        self.assertContains(response,'classes',count=2)
        self.assertContains(response,'magicitems',count=2)
        self.assertContains(response,'weapons',count=2)
        self.assertContains(response,'armor',count=2)
        self.assertContains(response,'search',count=2)

    def test_options_root_data(self):
        # Testing the actual content of the response data.
        response = self.client.get(f'/?format=json', REQUEST_METHOD='OPTIONS')
        self.assertEqual(response.json()['name'],'Api Root')
        self.assertEqual(response.json()['description'],'The default basic root view for DefaultRouter')
        self.assertEqual(response.json()['renders'],["application/json","text/html"])
        self.assertEqual(response.json()['parses'],["application/json","application/x-www-form-urlencoded","multipart/form-data"])

class ManifestTestCase(APITestCase):
    def setUp(self):
        from api.management.commands.importer import Importer
        from pathlib import Path
        filepath = 'test_filepath'
        filehash = 'test_hash'
        i = Importer([])
        i.import_manifest(Path(filepath), filehash)

    def test_get_manifest_data(self):
        response = self.client.get(f'/manifest/?format=json')
        # Confirm the basic elements show up.
        self.assertContains(response,'count',count=1)
        self.assertContains(response,'next',count=1)
        self.assertContains(response,'previous',count=1)
        self.assertContains(response,'results',count=1)

        # Confirm the values appear as expected.
        self.assertEqual(response.json()['count'],1)
        self.assertEqual(response.json()['results'][0]['filename'],'test_filepath')
        self.assertEqual(response.json()['results'][0]['type'],'test_filepath')
        self.assertEqual(response.json()['results'][0]['hash'],'test_hash')
        self.assertContains(response,'created_at', count=1)
        
    def test_options_manifest_data(self):
        response = self.client.get(f'/manifest/?format=json', REQUEST_METHOD='OPTIONS')
        self.assertEqual(response.json()['name'],'Manifest List')
        self.assertIn('API endpoint for returning a list of of manifests.',response.json()['description'])
        self.assertEqual(response.json()['renders'],["application/json","text/html"])
        self.assertEqual(response.json()['parses'],["application/json","application/x-www-form-urlencoded","multipart/form-data"])

class MonstersTestCase(APITestCase):
    def setUp(self):
        from api.management.commands.importer import Importer
        from api.management.commands.importer import ImportSpec
        from api.management.commands.importer import ImportOptions
        from pathlib import Path

        self.test_document_json = """
            {
            "title": "Test Reference Document",
            "slug": "test-doc",
            "desc": "This is a test document",
            "license": "Open Gaming License",
            "author": "John Doe",
            "organization": "Open5e Test Org",
            "version": "9.9",
            "copyright": "",
            "url": "http://example.com"
            }
        """

        self.test_monster_json = """
        {
            "name": "Goblin",
            "size": "Small",
            "type": "humanoid",
            "group": "Bad Guys",
            "subtype": "goblinoid",
            "alignment": "neutral evil",
            "armor_class": 15,
            "hit_points": 7,
            "hit_dice": "2d6",
            "speed": "30 ft.",
            "strength": 8,
            "dexterity": 14,
            "constitution": 10,
            "intelligence": 10,
            "wisdom": 8,
            "charisma": 8,
            "stealth": 6,
            "damage_vulnerabilities": "",
            "damage_resistances": "",
            "damage_immunities": "",
            "condition_immunities": "",
            "senses": "darkvision 60 ft., passive Perception 9",
            "languages": "Common, Goblin",
            "challenge_rating": "1/4",
            "special_abilities": [
                {
                    "name": "Nimble Escape",
                    "desc": "The goblin can take the Disengage or Hide action as a bonus action on each of its turns.",
                    "attack_bonus": 0
                }
            ],
            "actions": [
                {
                    "name": "Scimitar",
                    "desc": "Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 5 (1d6 + 2) slashing damage.",
                    "attack_bonus": 4,
                    "damage_dice": "1d6",
                    "damage_bonus": 2
                },
                {
                    "name": "Shortbow",
                    "desc": "Ranged Weapon Attack: +4 to hit, range 80/320 ft., one target. Hit: 5 (1d6 + 2) piercing damage.",
                    "attack_bonus": 4,
                    "damage_dice": "1d6",
                    "damage_bonus": 2
                }
            ],
            "speed_json": {
                "walk": 30
            },
            "armor_desc": "leather armor, shield",
            "page_no": 315
        }
        """
        i = Importer(ImportOptions(update=True, append=False, testrun=False))
        i.import_document(json.loads(self.test_document_json),ImportSpec("test_filename","test_model_class","import_monster"))
        i.import_monster(json.loads(self.test_monster_json),ImportSpec("test_filename","test_model_class","import_monster"))

    def test_get_monsters(self):
        response = self.client.get(f'/monsters/?format=json')
        # Confirm the basic elements show up.
        self.assertContains(response,'count',count=1)
        self.assertContains(response,'next',count=1)
        self.assertContains(response,'previous',count=1)
        self.assertContains(response,'results',count=1)        

    def test_get_monster_data(self):
        response = self.client.get(f'/monsters/?format=json')        
        self.assertEqual(response.json()['count'],1)
        in_goblin = json.loads(self.test_monster_json)
        out_goblin = response.json()['results'][0]

        self.assertEqual(in_goblin['name'], out_goblin['name'])
        self.assertEqual(in_goblin['size'], out_goblin['size'])
        self.assertEqual(in_goblin['type'], out_goblin['type'])
        self.assertEqual(in_goblin['subtype'], out_goblin['subtype'])
        self.assertEqual(in_goblin['group'], out_goblin['group']) #Not in original goblin
        self.assertEqual(in_goblin['alignment'], out_goblin['alignment'])
        self.assertEqual(in_goblin['armor_class'], out_goblin['armor_class'])
        self.assertEqual(in_goblin['armor_desc'], out_goblin['armor_desc'])
        self.assertEqual(in_goblin['hit_points'], out_goblin['hit_points'])
        self.assertEqual(in_goblin['hit_dice'], out_goblin['hit_dice'])
        self.assertEqual(in_goblin['speed_json'], out_goblin['speed']) #INPUT IS FORCED TO SPEED_JSON
        
        self.assertEqual(in_goblin['strength'], out_goblin['strength'])
        self.assertEqual(in_goblin['dexterity'], out_goblin['dexterity'])
        self.assertEqual(in_goblin['constitution'], out_goblin['constitution'])
        self.assertEqual(in_goblin['intelligence'], out_goblin['intelligence'])
        self.assertEqual(in_goblin['wisdom'], out_goblin['wisdom'])
        self.assertEqual(in_goblin['charisma'], out_goblin['charisma'])
        
        self.assertEqual(None, out_goblin['strength_save'])
        self.assertEqual(None, out_goblin['dexterity_save'])
        self.assertEqual(None, out_goblin['constitution_save'])
        self.assertEqual(None, out_goblin['intelligence_save'])
        self.assertEqual(None, out_goblin['wisdom_save'])
        self.assertEqual(None, out_goblin['charisma_save'])

        self.assertEqual(None, out_goblin['perception'])
        self.assertEqual(in_goblin['stealth'], out_goblin['skills']['stealth']) # MISALIGNED
        self.assertEqual(in_goblin['damage_vulnerabilities'], out_goblin['damage_vulnerabilities'])
        self.assertEqual(in_goblin['damage_resistances'], out_goblin['damage_resistances'])
        self.assertEqual(in_goblin['condition_immunities'], out_goblin['condition_immunities'])
        self.assertEqual(in_goblin['senses'], out_goblin['senses'])
        self.assertEqual(in_goblin['languages'], out_goblin['languages'])
        
        self.assertEqual(in_goblin['challenge_rating'], out_goblin['challenge_rating'])

        self.assertEqual(in_goblin['actions'], out_goblin['actions'])
        self.assertEqual("", out_goblin['reactions']) #Empty string?
        self.assertEqual("", out_goblin['legendary_desc']) #Empty string?
        self.assertEqual("", out_goblin['legendary_actions'])#Empty string?
        self.assertEqual(in_goblin['special_abilities'][0]['name'], out_goblin['special_abilities'][0]['name'])
        self.assertEqual(in_goblin['special_abilities'][0]['desc'], out_goblin['special_abilities'][0]['desc'])
        self.assertEqual([], out_goblin['spell_list']) #Empty list

        self.assertEqual(in_goblin['page_no'], out_goblin['page_no'])