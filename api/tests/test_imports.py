"""Test cases for the django API."""
import json

from pathlib import Path

from rest_framework.test import APITestCase

from api.management.commands.importer import Importer
from api.management.commands.importer import ImportSpec
from api.management.commands.importer import ImportOptions

from api.models import Subrace

# Create your tests here.


class APIRootTest(APITestCase):
    """Test cases for testing the / root of the API."""

    def test_get_root_headers(self):
        """Server response headers from the API root."""
        response = self.client.get(f'/?format=json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['allow'], 'GET, HEAD, OPTIONS')
        self.assertEqual(response.headers['content-type'], 'application/json')
        self.assertEqual(response.headers['X-Frame-Options'], 'DENY')
        self.assertEqual(response.headers['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(response.headers['Referrer-Policy'], 'same-origin')

    def test_get_root_list(self):
        """
        Confirm the list of resources available at the root.

        Checks the response for each of the known endpoints.
        Two results, one for the name, one for the link.
        """
        response = self.client.get(f'/?format=json')

        self.assertContains(response, 'manifest', count=2)
        self.assertContains(response, 'spells', count=2)
        self.assertContains(response, 'monsters', count=2)
        self.assertContains(response, 'documents', count=2)
        self.assertContains(response, 'backgrounds', count=2)
        self.assertContains(response, 'planes', count=2)
        self.assertContains(response, 'sections', count=2)
        self.assertContains(response, 'feats', count=2)
        self.assertContains(response, 'conditions', count=2)
        self.assertContains(response, 'races', count=2)
        self.assertContains(response, 'classes', count=2)
        self.assertContains(response, 'magicitems', count=2)
        self.assertContains(response, 'weapons', count=2)
        self.assertContains(response, 'armor', count=2)
        self.assertContains(response, 'search', count=2)

    def test_options_root_data(self):
        """
        Confirm the OPTIONS response available at the root.

        Checks the response for each of known values.
        """
        response = self.client.get(f'/?format=json', REQUEST_METHOD='OPTIONS')
        self.assertEqual(response.json()['name'], 'Api Root')
        self.assertEqual(
            response.json()['description'],
            'The default basic root view for DefaultRouter')
        self.assertEqual(
            response.json()['renders'], [
                "application/json", "text/html"])
        self.assertEqual(
            response.json()['parses'], [
                "application/json",
                "application/x-www-form-urlencoded",
                "multipart/form-data"])


class ManifestTestCase(APITestCase):
    """Test case for the manifest endpoint."""

    def setUp(self):
        """Build out a test manifest object."""
        from api.management.commands.importer import Importer
        from pathlib import Path
        filepath = 'test_filepath'
        filehash = 'test_hash'
        i = Importer([])
        i.import_manifest(Path(filepath), filehash)

    def test_get_manifest_data(self):
        """Confirm the manifest list response is structured correctly."""
        response = self.client.get(f'/manifest/?format=json')

        self.assertContains(response, 'count', count=1)
        self.assertContains(response, 'next', count=1)
        self.assertContains(response, 'previous', count=1)
        self.assertContains(response, 'results', count=1)

        self.assertEqual(response.json()['count'], 1)
        self.assertEqual(
            response.json()['results'][0]['filename'],
            'test_filepath')
        self.assertEqual(
            response.json()['results'][0]['type'],
            'test_filepath')
        self.assertEqual(response.json()['results'][0]['hash'], 'test_hash')
        self.assertContains(response, 'created_at', count=1)

    def test_options_manifest_data(self):
        """Confirm the manifest response item is correctly formatted."""
        response = self.client.get(
            f'/manifest/?format=json',
            REQUEST_METHOD='OPTIONS')
        self.assertEqual(response.json()['name'], 'Manifest List')
        self.assertIn(
            'API endpoint for returning a list of of manifests.',
            response.json()['description'])
        self.assertEqual(
            response.json()['renders'], [
                "application/json", "text/html"])
        self.assertEqual(
            response.json()['parses'], [
                "application/json",
                "application/x-www-form-urlencoded",
                "multipart/form-data"])


class SpellsTestCase(APITestCase):
    """Testing for the spells API endpoint."""

    def setUp(self):
        """Create the spell endpoint test data."""
        from api.management.commands.importer import Importer
        from api.management.commands.importer import ImportSpec
        from api.management.commands.importer import ImportOptions
        from pathlib import Path
        import json

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
        self.test_spell_json = """
            {
            "name": "Magic Missile",
            "desc": "You create three glowing darts of magical force. Each dart hits a creature of your choice that you can see within range. A dart deals 1d4 + 1 force damage to its target. The darts all strike simultaneously, and you can direct them to hit one creature or several.",
            "higher_level": "When you cast this spell using a spell slot of 2nd level or higher, the spell creates one more dart for each slot level above 1st.",
            "page": "phb 257",
            "range": "120 feet",
            "components": "V, S",
            "ritual": "no",
            "duration": "Instantaneous",
            "concentration": "no",
            "casting_time": "1 action",
            "level": "1st-level",
            "level_int": 1,
            "school": "Evocation",
            "class": "Sorcerer, Wizard"
            }
        """
        i = Importer(ImportOptions(update=True, append=False, testrun=False))
        i.import_document(
            json.loads(
                self.test_document_json),
            ImportSpec(
                "test_filename",
                "test_model_class",
                "import_spell"))
        i.import_spell(
            json.loads(
                self.test_spell_json),
            ImportSpec(
                "test_filename",
                "test_model_class",
                "import_spell"))

    def test_get_spells(self):
        """Confirm that the list result has the proper elements."""
        response = self.client.get(f'/spells/?format=json')
        self.assertContains(response, 'count', count=1)
        self.assertContains(response, 'next', count=1)
        self.assertContains(response, 'previous', count=1)
        self.assertContains(response, 'results', count=1)

    def test_get_spell_data(self):
        """Confirm that the result itself has the proper formatting and values."""
        import json
        response = self.client.get(f'/spells/?format=json')

        in_spell = json.loads(self.test_spell_json)
        out_spell = response.json()['results'][0]

        equal_fields = [
            'name',
            'desc',
            'higher_level',
            'page',
            'range',
            'components',
            'ritual',
            'duration',
            'concentration',
            'casting_time',
            'level',
            'level_int',
            'school']
        unequal_fields = [('class', 'dnd_class')]

        for field_name in equal_fields:
            self.assertEqual(
                in_spell[field_name],
                out_spell[field_name],
                f'Mismatched value of: {field_name}')

        for field_names in unequal_fields:
            self.assertEqual(in_spell[field_names[0]],
                             out_spell[field_names[1]],
                             f'Mismatched value of unequal field: {field_names}')


class SpellListTestCase(APITestCase):
    """Testing for the spell list API endpoint."""

    def setUp(self):
        """Create the spell endpoint test data."""
        from api.management.commands.importer import Importer
        from api.management.commands.importer import ImportSpec
        from api.management.commands.importer import ImportOptions
        from pathlib import Path
        import json

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
        self.test_spell_json = """
            {
            "name": "Magic Missile",
            "desc": "You create three glowing darts of magical force. Each dart hits a creature of your choice that you can see within range. A dart deals 1d4 + 1 force damage to its target. The darts all strike simultaneously, and you can direct them to hit one creature or several.",
            "higher_level": "When you cast this spell using a spell slot of 2nd level or higher, the spell creates one more dart for each slot level above 1st.",
            "page": "phb 257",
            "range": "120 feet",
            "components": "V, S",
            "ritual": "no",
            "duration": "Instantaneous",
            "concentration": "no",
            "casting_time": "1 action",
            "level": "1st-level",
            "level_int": 1,
            "school": "Evocation",
            "class": "Sorcerer, Wizard"
            }
        """

        self.test_spell_list_json = """
        {
        "name":"wizard",
        "spell_list":[
            "magic-missile"
        ]
        }
        
        
        """
        i = Importer(ImportOptions(update=True, append=False, testrun=False))
        i.import_document(
            json.loads(
                self.test_document_json),
            ImportSpec(
                "test_filename",
                "test_model_class",
                "import_spell"))
        i.import_spell(
            json.loads(
                self.test_spell_json),
            ImportSpec(
                "test_filename",
                "test_model_class",
                "import_spell"))

    

class MonstersTestCase(APITestCase):
    """Test case for the monster API endpoint."""

    def setUp(self):
        """Create a test document and monster."""
        from api.management.commands.importer import Importer
        from api.management.commands.importer import ImportSpec
        from api.management.commands.importer import ImportOptions
        from pathlib import Path
        import json

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
        i.import_document(
            json.loads(
                self.test_document_json),
            ImportSpec(
                "test_filename",
                "test_model_class",
                "import_monster"))
        i.import_monster(
            json.loads(
                self.test_monster_json),
            ImportSpec(
                "test_filename",
                "test_model_class",
                "import_monster"))

    def test_get_monsters(self):
        """Testing the monster list API endpoint."""
        response = self.client.get(f'/monsters/?format=json')
        # Confirm the basic elements show up.
        self.assertContains(response, 'count', count=1)
        self.assertContains(response, 'next', count=1)
        self.assertContains(response, 'previous', count=1)
        self.assertContains(response, 'results', count=1)

    def test_get_monster_data(self):
        """Testing the individual monster object response."""
        response = self.client.get(f'/monsters/?format=json')
        self.assertEqual(response.json()['count'], 1)

        in_monster = json.loads(self.test_monster_json)
        out_monster = response.json()['results'][0]

        equal_fields = [
            'name',
            'size',
            'type',
            'subtype',
            'group',
            'alignment',
            'armor_class',
            'armor_desc',
            'hit_points',
            'hit_dice',
            'strength',
            'dexterity',
            'constitution',
            'intelligence',
            'wisdom',
            'charisma',
            'damage_vulnerabilities',
            'damage_resistances',
            'condition_immunities',
            'senses',
            'languages',
            'challenge_rating',
            'actions',
            'page_no']

        unequal_fields = [
            ('speed_json', 'speed')]

        for field_name in equal_fields:
            self.assertEqual(
                in_monster[field_name],
                out_monster[field_name],
                f'Mismatched value of: {field_name}')

        for field_names in unequal_fields:
            self.assertEqual(
                in_monster[field_names[0]],
                out_monster[field_names[1]],
                f'Mismatched value of unequal field: {field_names}'
            )

        # Various one-offs that could probably all get bugfixed.
        self.assertEqual(None, out_monster['strength_save'])
        self.assertEqual(None, out_monster['dexterity_save'])
        self.assertEqual(None, out_monster['constitution_save'])
        self.assertEqual(None, out_monster['intelligence_save'])
        self.assertEqual(None, out_monster['wisdom_save'])
        self.assertEqual(None, out_monster['charisma_save'])
        self.assertEqual(None, out_monster['perception'])

        self.assertEqual(
            in_monster['stealth'],
            out_monster['skills']['stealth'])  # MISALIGNED
        self.assertEqual("", out_monster['reactions'])  # Empty string?
        self.assertEqual("", out_monster['legendary_desc'])  # Empty string?
        self.assertEqual("", out_monster['legendary_actions'])  # Empty string?
        self.assertEqual(
            in_monster['special_abilities'][0]['name'],
            out_monster['special_abilities'][0]['name'])
        self.assertEqual(
            in_monster['special_abilities'][0]['desc'],
            out_monster['special_abilities'][0]['desc'])
        self.assertEqual([], out_monster['spell_list'])  # Empty list


class DocumentsTestCase(APITestCase):
    """Test case for documents presented by the API."""

    def setUp(self):
        """Create a test document."""
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

        i = Importer(ImportOptions(update=True, append=False, testrun=False))
        i.import_document(
            json.loads(
                self.test_document_json),
            ImportSpec(
                "test_filename",
                "test_model_class",
                "import_document"))

    def test_get_documents(self):
        """Test the list of documents response."""
        response = self.client.get(f'/documents/?format=json')
        # Confirm the basic elements show up.
        self.assertContains(response, 'count', count=1)
        self.assertContains(response, 'next', count=1)
        self.assertContains(response, 'previous', count=1)
        self.assertContains(response, 'results', count=1)

    def test_get_document_data(self):
        """Test and individual document object's response."""
        response = self.client.get(f'/documents/?format=json')

        in_document = json.loads(self.test_document_json)
        out_document = response.json()['results'][0]

        equal_fields = [
            'title',
            'slug',
            'url',
            'license',
            'desc',
            'author',
            'organization',
            'version',
            'copyright']

        for field_name in equal_fields:
            self.assertEqual(
                in_document[field_name],
                out_document[field_name],
                f'Mismatched value of: {field_name}')


class CharClassTestCase(APITestCase):
    """Test case to confirm that CharClass and Archetype are displayed."""

    def setUp(self):
        """Create a document, charclass and related archetype."""
        from api.models import Archetype

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

        self.test_charclass_json = """{
        "name": "Bard",
        "features": {
            "hit-dice": "1d8",
            "hp-at-1st-level": "8 + your Constitution modifier",
            "hp-at-higher-levels": "1d8 (or 5) + your Constitution modifier per bard level after 1st",
            "prof-armor": "Light armor",
            "prof-weapons": "Simple weapons, hand crossbows, longswords, rapiers, shortswords",
            "prof-tools": "Three musical instruments of your choice",
            "prof-saving-throws": "Dexterity, Charisma",
            "prof-skills": "Choose any three",
            "equipment": "You start with the following equipment, in addition to the equipment granted by your background: \n \n* (*a*) a rapier, (*b*) a longsword, or (*c*) any simple weapon \n* (*a*) a diplomat's pack or (*b*) an entertainer's pack \n* (*a*) a lute or (*b*) any other musical instrument \n* Leather armor and a dagger",
            "table": "| Level | Proficiency Bonus | Features                                             | Spells Known | Cantrips Known | 1st | 2nd | 3rd | 4th | 5th | 6th | 7th | 8th | 9th | \n|-------|------------------|------------------------------------------------------|--------------|----------------|-----|-----|-----|-----|-----|-----|-----|-----|-----| \n| 1st   | +2               | Spellcasting, Bardic Inspiration (d6)                | 2            | 4              | 2   | -   | -   | -   | -   | -   | -   | -   | -   | \n| 2nd   | +2               | Jack of All Trades, Song of Rest (d6)                | 2            | 5              | 3   | -   | -   | -   | -   | -   | -   | -   | -   | \n| 3rd   | +2               | Bard College, Expertise                              | 2            | 6              | 4   | 2   | -   | -   | -   | -   | -   | -   | -   | \n| 4th   | +2               | Ability Score Improvement                            | 3            | 7              | 4   | 3   | -   | -   | -   | -   | -   | -   | -   | \n| 5th   | +3               | Bardic Inspiration (d8), Font of Inspiration         | 3            | 8              | 4   | 3   | 2   | -   | -   | -   | -   | -   | -   | \n| 6th   | +3               | Countercharm, Bard College Feature                   | 3            | 9              | 4   | 3   | 3   | -   | -   | -   | -   | -   | -   | \n| 7th   | +3               | -                                                    | 3            | 10             | 4   | 3   | 3   | 1   | -   | -   | -   | -   | -   | \n| 8th   | +3               | Ability Score Improvement                            | 3            | 11             | 4   | 3   | 3   | 2   | -   | -   | -   | -   | -   | \n| 9th   | +4               | Song of Rest (d8)                                    | 3            | 12             | 4   | 3   | 3   | 3   | 1   | -   | -   | -   | -   | \n| 10th  | +4               | Bardic Inspiration (d10), Expertise, Magical Secrets | 4            | 14             | 4   | 3   | 3   | 3   | 2   | -   | -   | -   | -   | \n| 11th  | +4               | -                                                    | 4            | 15             | 4   | 3   | 3   | 3   | 2   | 1   | -   | -   | -   | \n| 12th  | +4               | Ability Score Improvement                            | 4            | 15             | 4   | 3   | 3   | 3   | 2   | 1   | -   | -   | -   | \n| 13th  | +5               | Song of Rest (d10)                                   | 4            | 16             | 4   | 3   | 3   | 3   | 2   | 1   | 1   | -   | -   | \n| 14th  | +5               | Magical Secrets, Bard College Feature                | 4            | 18             | 4   | 3   | 3   | 3   | 2   | 1   | 1   | -   | -   | \n| 15th  | +5               | Bardic Inspiration (d12)                             | 4            | 19             | 4   | 3   | 3   | 3   | 2   | 1   | 1   | 1   | -   | \n| 16th  | +5               | Ability Score Improvement                            | 4            | 19             | 4   | 3   | 3   | 3   | 2   | 1   | 1   | 1   | -   | \n| 17th  | +6               | Song of Rest (d12)                                   | 4            | 20             | 4   | 3   | 3   | 3   | 2   | 1   | 1   | 1   | 1   | \n| 18th  | +6               | Magical Secrets                                      | 4            | 22             | 4   | 3   | 3   | 3   | 3   | 1   | 1   | 1   | 1   | \n| 19th  | +6               | Ability Score Improvement                            | 4            | 22             | 4   | 3   | 3   | 3   | 3   | 2   | 1   | 1   | 1   | \n| 20th  | +6               | Superior Inspiration                                 | 4            | 22             | 4   | 3   | 3   | 3   | 3   | 2   | 2   | 1   | 1   | ",
            "desc": "### Spellcasting \n \nYou have learned to untangle and reshape the fabric of reality in harmony with your wishes and music. \n \nYour spells are part of your vast repertoire, magic that you can tune to different situations. \n \n#### Cantrips \n \nYou know two cantrips of your choice from the bard spell list. You learn additional bard cantrips of your choice at higher levels, as shown in the Cantrips Known column of the Bard table. \n \n#### Spell Slots \n \nThe Bard table shows how many spell slots you have to cast your spells of 1st level and higher. To cast one of these spells, you must expend a slot of the spell's level or higher. You regain all expended spell slots when you finish a long rest. \n \nFor example, if you know the 1st-level spell *cure wounds* and have a 1st-level and a 2nd-level spell slot available, you can cast *cure wounds* using either slot. \n \n#### Spells Known of 1st Level and Higher \n \nYou know four 1st-level spells of your choice from the bard spell list. \n \nThe Spells Known column of the Bard table shows when you learn more bard spells of your choice. Each of these spells must be of a level for which you have spell slots, as shown on the table. For instance, when you reach 3rd level in this class, you can learn one new spell of 1st or 2nd level. \n \nAdditionally, when you gain a level in this class, you can choose one of the bard spells you know and replace it with another spell from the bard spell list, which also must be of a level for which you have spell slots. \n \n#### Spellcasting Ability \n \nCharisma is your spellcasting ability for your bard spells. Your magic comes from the heart and soul you pour into the performance of your music or oration. You use your Charisma whenever a spell refers to your spellcasting ability. In addition, you use your Charisma modifier when setting the saving throw DC for a bard spell you cast and when making an attack roll with one. \n \n**Spell save DC** = 8 + your proficiency bonus + your Charisma modifier \n \n**Spell attack modifier** = your proficiency bonus + your Charisma modifier \n \n#### Ritual Casting \n \nYou can cast any bard spell you know as a ritual if that spell has the ritual tag. \n \n#### Spellcasting Focus \n \nYou can use a musical instrument (see chapter 5, “Equipment”) as a spellcasting focus for your bard spells. \n \n### Bardic Inspiration \n \nYou can inspire others through stirring words or music. To do so, you use a bonus action on your turn to choose one creature other than yourself within 60 feet of you who can hear you. That creature gains one Bardic Inspiration die, a d6. \n \nOnce within the next 10 minutes, the creature can roll the die and add the number rolled to one ability check, attack roll, or saving throw it makes. The creature can wait until after it rolls the d20 before deciding to use the Bardic Inspiration die, but must decide before the GM says whether the roll succeeds or fails. Once the Bardic Inspiration die is rolled, it is lost. A creature can have only one Bardic Inspiration die at a time. \n \nYou can use this feature a number of times equal to your Charisma modifier (a minimum of once). You regain any expended uses when you finish a long rest. \n \nYour Bardic Inspiration die changes when you reach certain levels in this class. The die becomes a d8 at 5th level, a d10 at 10th level, and a d12 at 15th level. \n \n### Jack of All Trades \n \nStarting at 2nd level, you can add half your proficiency bonus, rounded down, to any ability check you make that doesn't already include your proficiency bonus. \n \n### Song of Rest \n \nBeginning at 2nd level, you can use soothing music or oration to help revitalize your wounded allies during a short rest. If you or any friendly creatures who can hear your performance regain hit points at the end of the short rest by spending one or more Hit Dice, each of those creatures regains an extra 1d6 hit points. \n \nThe extra hit points increase when you reach certain levels in this class: to 1d8 at 9th level, to 1d10 at 13th level, and to 1d12 at 17th level. \n \n### Bard College \n \nAt 3rd level, you delve into the advanced techniques of a bard college of your choice: the College of Lore or the College of Valor, both detailed at the end of \n \nthe class description. Your choice grants you features at 3rd level and again at 6th and 14th level. \n \n### Expertise \n \nAt 3rd level, choose two of your skill proficiencies. Your proficiency bonus is doubled for any ability check you make that uses either of the chosen proficiencies. \n \nAt 10th level, you can choose another two skill proficiencies to gain this benefit. \n \n### Ability Score Improvement \n \nWhen you reach 4th level, and again at 8th, 12th, 16th, and 19th level, you can increase one ability score of your choice by 2, or you can increase two ability scores of your choice by 1. As normal, you can't increase an ability score above 20 using this feature. \n \n### Font of Inspiration \n \nBeginning when you reach 5th level, you regain all of your expended uses of Bardic Inspiration when you finish a short or long rest. \n \n### Countercharm \n \nAt 6th level, you gain the ability to use musical notes or words of power to disrupt mind-influencing effects. As an action, you can start a performance that lasts until the end of your next turn. During that time, you and any friendly creatures within 30 feet of you have advantage on saving throws against being frightened or charmed. A creature must be able to hear you to gain this benefit. The performance ends early if you are incapacitated or silenced or if you voluntarily end it (no action required). \n \n### Magical Secrets \n \nBy 10th level, you have plundered magical knowledge from a wide spectrum of disciplines. Choose two spells from any class, including this one. A spell you choose must be of a level you can cast, as shown on the Bard table, or a cantrip. \n \nThe chosen spells count as bard spells for you and are included in the number in the Spells Known column of the Bard table. \n \nYou learn two additional spells from any class at 14th level and again at 18th level. \n \n### Superior Inspiration \n \nAt 20th level, when you roll initiative and have no uses of Bardic Inspiration left, you regain one use.",
            "spellcasting-ability": "Charisma"
        },
        "subtypes-name": "Colleges",
        "subtypes": [
            {
                "name": "College of Lore",
                "desc": "Bards of the College of Lore know something about most things, collecting bits of knowledge from sources as diverse as scholarly tomes and peasant tales. Whether singing folk ballads in taverns or elaborate compositions in royal courts, these bards use their gifts to hold audiences spellbound. When the applause dies down, the audience members might find themselves questioning everything they held to be true, from their faith in the priesthood of the local temple to their loyalty to the king. \n \nThe loyalty of these bards lies in the pursuit of beauty and truth, not in fealty to a monarch or following the tenets of a deity. A noble who keeps such a bard as a herald or advisor knows that the bard would rather be honest than politic. \n \nThe college's members gather in libraries and sometimes in actual colleges, complete with classrooms and dormitories, to share their lore with one another. They also meet at festivals or affairs of state, where they can expose corruption, unravel lies, and poke fun at self-important figures of authority. \n \n##### Bonus Proficiencies \n \nWhen you join the College of Lore at 3rd level, you gain proficiency with three skills of your choice. \n \n##### Cutting Words \n \nAlso at 3rd level, you learn how to use your wit to distract, confuse, and otherwise sap the confidence and competence of others. When a creature that you can see within 60 feet of you makes an attack roll, an ability check, or a damage roll, you can use your reaction to expend one of your uses of Bardic Inspiration, rolling a Bardic Inspiration die and subtracting the number rolled from the creature's roll. You can choose to use this feature after the creature makes its roll, but before the GM determines whether the attack roll or ability check succeeds or fails, or before the creature deals its damage. The creature is immune if it can't hear you or if it's immune to being charmed. \n \n##### Additional Magical Secrets \n \nAt 6th level, you learn two spells of your choice from any class. A spell you choose must be of a level you can cast, as shown on the Bard table, or a cantrip. The chosen spells count as bard spells for you but don't count against the number of bard spells you know. \n \n##### Peerless Skill \n \nStarting at 14th level, when you make an ability check, you can expend one use of Bardic Inspiration. Roll a Bardic Inspiration die and add the number rolled to your ability check. You can choose to do so after you roll the die for the ability check, but before the GM tells you whether you succeed or fail."
            }
        ]
    }
        """

        i = Importer(ImportOptions(update=True, append=False, testrun=False))
        i.import_document(
            json.loads(
                self.test_document_json),
            ImportSpec(
                "test_filename",
                "test_model_class",
                "import_monster"))
        i.import_class(
            json.loads(self.test_charclass_json, strict=False),
            ImportSpec(
                "test_filename",
                "test_model_class",
                "import_class",
                sub_spec=ImportSpec(
                    "test_filename",
                    Archetype,
                    i.import_archetype
                )
            )
        )

    def test_get_classes(self):
        """Get a list of classes and test the list object."""
        response = self.client.get(f'/classes/?format=json')

        # Confirm the basic elements show up.
        self.assertContains(response, 'count', count=4)
        self.assertContains(response, 'next', count=3)
        self.assertContains(response, 'previous', count=1)
        self.assertContains(response, 'results', count=1)

    def test_get_class_data(self):
        """Get an individual object and test values."""
        response = self.client.get(f'/classes/?format=json')

        in_class = json.loads(self.test_charclass_json, strict=False)
        out_class = response.json()['results'][0]

        self.assertEqual(in_class['name'], out_class['name'])
        # The Features key is not duplicated in the api
        self.assertEqual(in_class['features']['desc'], out_class['desc'])
        # dashes on entry, underscores out.
        self.assertEqual(
            in_class['features']['hit-dice'],
            out_class['hit_dice'])
        self.assertEqual(
            in_class['features']['hp-at-1st-level'],
            out_class['hp_at_1st_level'])
        self.assertEqual(
            in_class['features']['prof-armor'],
            out_class['prof_armor'])
        self.assertEqual(
            in_class['features']['prof-weapons'],
            out_class['prof_weapons'])
        self.assertEqual(
            in_class['features']['prof-saving-throws'],
            out_class['prof_saving_throws'])
        self.assertEqual(
            in_class['features']['prof-skills'],
            out_class['prof_skills'])
        self.assertEqual(
            in_class['features']['equipment'],
            out_class['equipment'])
        self.assertEqual(in_class['features']['table'], out_class['table'])
        self.assertEqual(
            in_class['features']['spellcasting-ability'],
            out_class['spellcasting_ability'])
        self.assertEqual(in_class['subtypes-name'], out_class['subtypes_name'])

        self.assertEqual(
            in_class['subtypes'][0]['name'],
            out_class['archetypes'][0]['name'])
        self.assertEqual(
            in_class['subtypes'][0]['desc'],
            out_class['archetypes'][0]['desc'])


class BackgroundsTestCase(APITestCase):
    """Test case for Background API objects."""

    def setUp(self):
        """Create a document and background for testing."""
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

        self.test_background_json = r"""
            {
            "name": "Acolyte",
            "desc": "You have spent your life in the service of a temple to a specific god or pantheon of gods. You act as an intermediary between the realm of the holy and the mortal world, performing sacred rites and offering sacrifices in order to conduct worshipers into the presence of the divine. You are not necessarily a cleric-performing sacred rites is not the same thing as channeling divine power.\n\nChoose a god, a pantheon of gods, or some other quasi-divine being from among those listed in \"Fantasy-Historical Pantheons\" or those specified by your GM, and work with your GM to detail the nature of your religious service. Were you a lesser functionary in a temple, raised from childhood to assist the priests in the sacred rites? Or were you a high priest who suddenly experienced a call to serve your god in a different way? Perhaps you were the leader of a small cult outside of any established temple structure, or even an occult group that served a fiendish master that you now deny.",
            "skill-proficiencies": "Insight, Religion",
            "languages": "Two of your choice",
            "equipment": "A holy symbol (a gift to you when you entered the priesthood), a prayer book or prayer wheel, 5 sticks of incense, vestments, a set of common clothes, and a pouch containing 15 gp",
            "feature-name": "Shelter of the Faithful",
            "feature-desc": "As an acolyte, you command the respect of those who share your faith, and you can perform the religious ceremonies of your deity. You and your adventuring companions can expect to receive free healing and care at a temple, shrine, or other established presence of your faith, though you must provide any material components needed for spells. Those who share your religion will support you (but only you) at a modest lifestyle.\n\nYou might also have ties to a specific temple dedicated to your chosen deity or pantheon, and you have a residence there. This could be the temple where you used to serve, if you remain on good terms with it, or a temple where you have found a new home. While near your temple, you can call upon the priests for assistance, provided the assistance you ask for is not hazardous and you remain in good standing with your temple.",
            "suggested-characteristics": "Acolytes are shaped by their experience in temples or other religious communities. Their study of the history and tenets of their faith and their relationships to temples, shrines, or hierarchies affect their mannerisms and ideals. Their flaws might be some hidden hypocrisy or heretical idea, or an ideal or bond taken to an extreme.\n\n**Suggested Acolyte Characteristics (table)**\n\n| d8 | Personality Trait                                                                                                  |\n|----|--------------------------------------------------------------------------------------------------------------------|\n| 1  | I idolize a particular hero of my faith, and constantly refer to that person's deeds and example.                  |\n| 2  | I can find common ground between the fiercest enemies, empathizing with them and always working toward peace.      |\n| 3  | I see omens in every event and action. The gods try to speak to us, we just need to listen                         |\n| 4  | Nothing can shake my optimistic attitude.                                                                          |\n| 5  | I quote (or misquote) sacred texts and proverbs in almost every situation.                                         |\n| 6  | I am tolerant (or intolerant) of other faiths and respect (or condemn) the worship of other gods.                  |\n| 7  | I've enjoyed fine food, drink, and high society among my temple's elite. Rough living grates on me.                |\n| 8  | I've spent so long in the temple that I have little practical experience dealing with people in the outside world. |\n\n| d6 | Ideal                                                                                                                  |\n|----|------------------------------------------------------------------------------------------------------------------------|\n| 1  | Tradition. The ancient traditions of worship and sacrifice must be preserved and upheld. (Lawful)                      |\n| 2  | Charity. I always try to help those in need, no matter what the personal cost. (Good)                                  |\n| 3  | Change. We must help bring about the changes the gods are constantly working in the world. (Chaotic)                   |\n| 4  | Power. I hope to one day rise to the top of my faith's religious hierarchy. (Lawful)                                   |\n| 5  | Faith. I trust that my deity will guide my actions. I have faith that if I work hard, things will go well. (Lawful)    |\n| 6  | Aspiration. I seek to prove myself worthy of my god's favor by matching my actions against his or her teachings. (Any) |\n\n| d6 | Bond                                                                                     |\n|----|------------------------------------------------------------------------------------------|\n| 1  | I would die to recover an ancient relic of my faith that was lost long ago.              |\n| 2  | I will someday get revenge on the corrupt temple hierarchy who branded me a heretic.     |\n| 3  | I owe my life to the priest who took me in when my parents died.                         |\n| 4  | Everything I do is for the common people.                                                |\n| 5  | I will do anything to protect the temple where I served.                                 |\n| 6  | I seek to preserve a sacred text that my enemies consider heretical and seek to destroy. |\n\n| d6 | Flaw                                                                                          |\n|----|-----------------------------------------------------------------------------------------------|\n| 1  | I judge others harshly, and myself even more severely.                                        |\n| 2  | I put too much trust in those who wield power within my temple's hierarchy.                   |\n| 3  | My piety sometimes leads me to blindly trust those that profess faith in my god.              |\n| 4  | I am inflexible in my thinking.                                                               |\n| 5  | I am suspicious of strangers and expect the worst of them.                                    |\n| 6  | Once I pick a goal, I become obsessed with it to the detriment of everything else in my life. |"
            }
        """

        i = Importer(ImportOptions(update=True, append=False, testrun=False))
        i.import_document(
            json.loads(
                self.test_document_json),
            ImportSpec(
                "test_filename",
                "test_model_class",
                "import_background"))
        i.import_background(
            json.loads(
                self.test_background_json),
            ImportSpec(
                "test_filename",
                "test_model_class",
                "import_background"))

    def test_get_background_data(self):
        """Run the API response test for background."""
        response = self.client.get("/backgrounds/?format=json")

        in_background = json.loads(self.test_background_json)
        out_background = response.json()['results'][0]

        equal_fields = [
            'name',
            'desc',
            'languages',
            'equipment'
        ]

        unequal_fields = [
            ('skill-proficiencies', 'skill_proficiencies'),
            ('feature-name', 'feature'),
            ('feature-desc', 'feature_desc'),
            ('suggested-characteristics', 'suggested_characteristics')
        ]

        for field_name in equal_fields:
            self.assertEqual(
                in_background[field_name],
                out_background[field_name],
                f'Mismatched value of: {field_name}')

        for field_names in unequal_fields:
            self.assertEqual(in_background[field_names[0]],
                             out_background[field_names[1]],
                             f'Mismatched value of unequal field: {field_names}')


class PlanesTestCase(APITestCase):
    """Test case for Plane API objects."""

    def setUp(self):
        """Create a document and plane for testing."""
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

        self.test_plane_json = r"""
        {
        "name": "The Material Plane",
        "desc": "The Material Plane is the nexus where the philosophical and elemental forces that define the other planes collide in the jumbled existence of mortal life and mundane matter. All fantasy gaming worlds exist within the Material Plane, making it the starting point for most campaigns and adventures. The rest of the multiverse is defined in relation to the Material Plane.\nThe worlds of the Material Plane are infinitely diverse, for they reflect the creative imagination of the GMs who set their games there, as well as the players whose heroes adventure there. They include magic-wasted desert planets and island-dotted water worlds, worlds where magic combines with advanced technology and others trapped in an endless Stone Age, worlds where the gods walk and places they have abandoned."
        }
        """

        i = Importer(ImportOptions(update=True, append=False, testrun=False))
        i.import_document(
            json.loads(
                self.test_document_json),
            ImportSpec(
                "test_filename",
                "test_model_class",
                "import_plane"))
        i.import_plane(
            json.loads(
                self.test_plane_json, strict=False),
            ImportSpec(
                "test_filename",
                "test_model_class",
                "import_plane"))

    def test_get_plane_data(self):
        """Run the API response test for plane."""
        response = self.client.get("/planes/?format=json")

        in_plane = json.loads(self.test_plane_json)
        out_plane = response.json()['results'][0]

        equal_fields = [
            'name',
            'desc'
        ]

        for field_name in equal_fields:
            self.assertEqual(
                in_plane[field_name],
                out_plane[field_name],
                f'Mismatched value of: {field_name}')


class SectionsTestCase(APITestCase):
    """Test case for Section API objects."""

    def setUp(self):
        """Create a document and section for testing."""
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

        self.test_section_json = """
            {
            "name": "Traps",
            "desc": "Traps can be found almost anywhere. One wrong step in an ancient tomb might trigger a series of scything blades, which cleave through armor and bone. The seemingly innocuous vines that hang over a cave entrance might grasp and choke anyone who pushes through them. A net hidden among the trees might drop on travelers who pass underneath. In a fantasy game, unwary adventurers can fall to their deaths, be burned alive, or fall under a fusillade of poisoned darts.\n\nA trap can be either mechanical or magical in nature. **Mechanical traps** include pits, arrow traps, falling blocks, water-filled rooms, whirling blades, and anything else that depends on a mechanism to operate. **Magic traps** are either magical device traps or spell traps. Magical device traps initiate spell effects when activated. Spell traps are spells such as _glyph of warding_ and _symbol_ that function as traps.\n\n## Traps in Play\n\nWhen adventurers come across a trap, you need to know how the trap is triggered and what it does, as well as the possibility for the characters to detect the trap and to disable or avoid it.\n\n### Triggering a Trap\n\nMost traps are triggered when a creature goes somewhere or touches something that the trap's creator wanted to protect. Common triggers include stepping on a pressure plate or a false section of floor, pulling a trip wire, turning a doorknob, and using the wrong key in a lock. Magic traps are often set to go off when a creature enters an area or touches an object. Some magic traps (such as the _glyph of warding_ spell) have more complicated trigger conditions, including a password that prevents the trap from activating.\n\n### Detecting and Disabling a Trap\n\nUsually, some element of a trap is visible to careful inspection. Characters might notice an uneven flagstone that conceals a pressure plate, spot the gleam of light off a trip wire, notice small holes in the walls from which jets of flame will erupt, or otherwise detect something that points to a trap's presence.\n\nA trap's description specifies the checks and DCs needed to detect it, disable it, or both. A character actively looking for a trap can attempt a Wisdom (Perception) check against the trap's DC. You can also compare the DC to detect the trap with each character's passive Wisdom (Perception) score to determine whether anyone in the party notices the trap in passing. If the adventurers detect a trap before triggering it, they might be able to disarm it, either permanently or long enough to move past it. You might call for an Intelligence (Investigation) check for a character to deduce what needs to be done, followed by a Dexterity check using thieves' tools to perform the necessary sabotage.\n\nAny character can attempt an Intelligence (Arcana) check to detect or disarm a magic trap, in addition to any other checks noted in the trap's description. The DCs are the same regardless of the check used. In addition, _dispel magic_ has a chance of disabling most magic traps. A magic trap's description provides the DC for the ability check made when you use _dispel magic_.\n\nIn most cases, a trap's description is clear enough that you can adjudicate whether a character's actions locate or foil the trap. As with many situations, you shouldn't allow die rolling to override clever play and good planning. Use your common sense, drawing on the trap's description to determine what happens. No trap's design can anticipate every possible action that the characters might attempt.\n\nYou should allow a character to discover a trap without making an ability check if an action would clearly reveal the trap's presence. For example, if a character lifts a rug that conceals a pressure plate, the character has found the trigger and no check is required.\n\nFoiling traps can be a little more complicated. Consider a trapped treasure chest. If the chest is opened without first pulling on the two handles set in its sides, a mechanism inside fires a hail of poison needles toward anyone in front of it. After inspecting the chest and making a few checks, the characters are still unsure if it's trapped. Rather than simply open the chest, they prop a shield in front of it and push the chest open at a distance with an iron rod. In this case, the trap still triggers, but the hail of needles fires harmlessly into the shield.\n\nTraps are often designed with mechanisms that allow them to be disarmed or bypassed. Intelligent monsters that place traps in or around their lairs need ways to get past those traps without harming themselves. Such traps might have hidden levers that disable their triggers, or a secret door might conceal a passage that goes around the trap.\n\n### Trap Effects\n\nThe effects of traps can range from inconvenient to deadly, making use of elements such as arrows, spikes, blades, poison, toxic gas, blasts of fire, and deep pits. The deadliest traps combine multiple elements to kill, injure, contain, or drive off any creature unfortunate enough to trigger them. A trap's description specifies what happens when it is triggered.\n\nThe attack bonus of a trap, the save DC to resist its effects, and the damage it deals can vary depending on the trap's severity. Use the Trap Save DCs and Attack Bonuses table and the Damage Severity by Level table for suggestions based on three levels of trap severity.\n\nA trap intended to be a **setback** is unlikely to kill or seriously harm characters of the indicated levels, whereas a **dangerous** trap is likely to seriously injure (and potentially kill) characters of the indicated levels. A **deadly** trap is likely to kill characters of the indicated levels.\n\n**Trap Save DCs and Attack Bonuses (table)**\n| Trap Danger | Save DC | Attack Bonus |\n|-------------|---------|--------------|\n| Setback     | 10-11   | +3 to +5     |\n| Dangerous   | 12-15   | +6 to +8     |\n| Deadly      | 16-20   | +9 to +12    |\n**Damage Severity by Level (table)**\n| Character Level | Setback | Dangerous | Deadly |\n|-----------------|---------|-----------|--------|\n| 1st-4th         | 1d10    | 2d10      | 4d10   |\n| 5th-10th        | 2d10    | 4d10      | 10d10  |\n| 11th-16th       | 4d10    | 10d10     | 18d10  |\n| 17th-20th       | 10d10   | 18d10     | 24d10  |\n\n### Complex Traps\n\nComplex traps work like standard traps, except once activated they execute a series of actions each round. A complex trap turns the process of dealing with a trap into something more like a combat encounter.\n\nWhen a complex trap activates, it rolls initiative. The trap's description includes an initiative bonus. On its turn, the trap activates again, often taking an action. It might make successive attacks against intruders, create an effect that changes over time, or otherwise produce a dynamic challenge. Otherwise, the complex trap can be detected and disabled or bypassed in the usual ways.\n\nFor example, a trap that causes a room to slowly flood works best as a complex trap. On the trap's turn, the water level rises. After several rounds, the room is completely flooded.\n\n## Sample Traps\n\nThe magical and mechanical traps presented here vary in deadliness and are presented in alphabetical order.\n\n### Collapsing Roof\n\n_Mechanical trap_\n\nThis trap uses a trip wire to collapse the supports keeping an unstable section of a ceiling in place.\n\nThe trip wire is 3 inches off the ground and stretches between two support beams. The DC to spot the trip wire is 10. A successful DC 15 Dexterity check using thieves' tools disables the trip wire harmlessly. A character without thieves' tools can attempt this check with disadvantage using any edged weapon or edged tool. On a failed check, the trap triggers.\n\nAnyone who inspects the beams can easily determine that they are merely wedged in place. As an action, a character can knock over a beam, causing the trap to trigger.\n\nThe ceiling above the trip wire is in bad repair, and anyone who can see it can tell that it's in danger of collapse.\n\nWhen the trap is triggered, the unstable ceiling collapses. Any creature in the area beneath the unstable section must succeed on a DC 15 Dexterity saving throw, taking 22 (4d10) bludgeoning damage on a failed save, or half as much damage on a successful one. Once the trap is triggered, the floor of the area is filled with rubble and becomes difficult terrain.\n\n### Falling Net\n\n_Mechanical trap_\n\nThis trap uses a trip wire to release a net suspended from the ceiling.\n\nThe trip wire is 3 inches off the ground and stretches between two columns or trees. The net is hidden by cobwebs or foliage. The DC to spot the trip wire and net is 10. A successful DC 15 Dexterity check using thieves' tools breaks the trip wire harmlessly. A character without thieves' tools can attempt this check with disadvantage using any edged weapon or edged tool. On a failed check, the trap triggers.\n\nWhen the trap is triggered, the net is released, covering a 10-foot-square area. Those in the area are trapped under the net and restrained, and those that fail a DC 10 Strength saving throw are also knocked prone. A creature can use its action to make a DC 10\n\nStrength check, freeing itself or another creature within its reach on a success. The net has AC 10 and 20 hit points. Dealing 5 slashing damage to the net (AC 10) destroys a 5-foot-square section of it, freeing any creature trapped in that section.\n\n### Fire-Breathing Statue\n\n_Magic trap_\n\nThis trap is activated when an intruder steps on a hidden pressure plate, releasing a magical gout of flame from a nearby statue. The statue can be of anything, including a dragon or a wizard casting a spell.\n\nThe DC is 15 to spot the pressure plate, as well as faint scorch marks on the floor and walls. A spell or other effect that can sense the presence of magic, such as _detect magic_, reveals an aura of evocation magic around the statue.\n\nThe trap activates when more than 20 pounds of weight is placed on the pressure plate, causing the statue to release a 30-foot cone of fire. Each creature in the fire must make a DC 13 Dexterity saving throw, taking 22 (4d10) fire damage on a failed save, or half as much damage on a successful one.\n\nWedging an iron spike or other object under the pressure plate prevents the trap from activating. A successful _dispel magic_ (DC 13) cast on the statue destroys the trap.\n\n### Pits\n\n_Mechanical trap_\n\nFour basic pit traps are presented here.\n\n**_Simple Pit_**. A simple pit trap is a hole dug in the ground. The hole is covered by a large cloth anchored on the pit's edge and camouflaged with dirt and debris.\n\nThe DC to spot the pit is 10. Anyone stepping on the cloth falls through and pulls the cloth down into the pit, taking damage based on the pit's depth (usually 10 feet, but some pits are deeper).\n\n**_Hidden Pit_**. This pit has a cover constructed from material identical to the floor around it.\n\nA successful DC 15 Wisdom (Perception) check discerns an absence of foot traffic over the section of floor that forms the pit's cover. A successful DC 15 Intelligence (Investigation) check is necessary to confirm that the trapped section of floor is actually the cover of a pit.\n\nWhen a creature steps on the cover, it swings open like a trapdoor, causing the intruder to spill into the pit below. The pit is usually 10 or 20 feet deep but can be deeper.\n\nOnce the pit trap is detected, an iron spike or similar object can be wedged between the pit's cover and the surrounding floor in such a way as to prevent the cover from opening, thereby making it safe to cross. The cover can also be magically held shut using the _arcane lock_ spell or similar magic.\n\n**_Locking Pit_**. This pit trap is identical to a hidden pit trap, with one key exception: the trap door that covers the pit is spring-loaded. After a creature falls into the pit, the cover snaps shut to trap its victim inside.\n\nA successful DC 20 Strength check is necessary to pry the cover open. The cover can also be smashed open. A character in the pit can also attempt to disable the spring mechanism from the inside with a DC 15 Dexterity check using thieves' tools, provided that the mechanism can be reached and the character can see. In some cases, a mechanism (usually hidden behind a secret door nearby) opens the pit.\n\n**_Spiked Pit_**. This pit trap is a simple, hidden, or locking pit trap with sharpened wooden or iron spikes at the bottom. A creature falling into the pit takes 11 (2d10) piercing damage from the spikes, in addition to any falling damage. Even nastier versions have poison smeared on the spikes. In that case, anyone taking piercing damage from the spikes must also make a DC 13 Constitution saving throw, taking an 22 (4d10) poison damage on a failed save, or half as much damage on a successful one.\n\n### Poison Darts\n\n_Mechanical trap_\n\nWhen a creature steps on a hidden pressure plate, poison-tipped darts shoot from spring-loaded or pressurized tubes cleverly embedded in the surrounding walls. An area might include multiple pressure plates, each one rigged to its own set of darts.\n\nThe tiny holes in the walls are obscured by dust and cobwebs, or cleverly hidden amid bas-reliefs, murals, or frescoes that adorn the walls. The DC to spot them is 15. With a successful DC 15 Intelligence (Investigation) check, a character can deduce the presence of the pressure plate from variations in the mortar and stone used to create it, compared to the surrounding floor. Wedging an iron spike or other object under the pressure plate prevents the trap from activating. Stuffing the holes with cloth or wax prevents the darts contained within from launching.\n\nThe trap activates when more than 20 pounds of weight is placed on the pressure plate, releasing four darts. Each dart makes a ranged attack with a +8\n\nbonus against a random target within 10 feet of the pressure plate (vision is irrelevant to this attack roll). (If there are no targets in the area, the darts don't hit anything.) A target that is hit takes 2 (1d4) piercing damage and must succeed on a DC 15 Constitution saving throw, taking 11 (2d10) poison damage on a failed save, or half as much damage on a successful one.\n\n### Poison Needle\n\n_Mechanical trap_\n\nA poisoned needle is hidden within a treasure chest's lock, or in something else that a creature might open. Opening the chest without the proper key causes the needle to spring out, delivering a dose of poison.\n\nWhen the trap is triggered, the needle extends 3 inches straight out from the lock. A creature within range takes 1 piercing damage and 11\n\n(2d10) poison damage, and must succeed on a DC 15 Constitution saving throw or be poisoned for 1 hour.\n\nA successful DC 20 Intelligence (Investigation) check allows a character to deduce the trap's presence from alterations made to the lock to accommodate the needle. A successful DC 15 Dexterity check using thieves' tools disarms the trap, removing the needle from the lock. Unsuccessfully attempting to pick the lock triggers the trap.\n\n### Rolling Sphere\n\n_Mechanical trap_\n\nWhen 20 or more pounds of pressure are placed on this trap's pressure plate, a hidden trapdoor in the ceiling opens, releasing a 10-foot-diameter rolling sphere of solid stone.\n\nWith a successful DC 15 Wisdom (Perception) check, a character can spot the trapdoor and pressure plate. A search of the floor accompanied by a successful DC 15 Intelligence (Investigation) check reveals variations in the mortar and stone that betray the pressure plate's presence. The same check made while inspecting the ceiling notes variations in the stonework that reveal the trapdoor. Wedging an iron spike or other object under the pressure plate prevents the trap from activating.\n\nActivation of the sphere requires all creatures present to roll initiative. The sphere rolls initiative with a +8 bonus. On its turn, it moves 60 feet in a straight line. The sphere can move through creatures' spaces, and creatures can move through its space, treating it as difficult terrain. Whenever the sphere enters a creature's space or a creature enters its space while it's rolling, that creature must succeed on a DC 15 Dexterity saving throw or take 55 (10d10) bludgeoning damage and be knocked prone.\n\nThe sphere stops when it hits a wall or similar barrier. It can't go around corners, but smart dungeon builders incorporate gentle, curving turns into nearby passages that allow the sphere to keep moving.\n\nAs an action, a creature within 5 feet of the sphere can attempt to slow it down with a DC 20 Strength check. On a successful check, the sphere's speed is reduced by 15 feet. If the sphere's speed drops to 0, it stops moving and is no longer a threat.\n\n### Sphere of Annihilation\n\n_Magic trap_\n\nMagical, impenetrable darkness fills the gaping mouth of a stone face carved into a wall. The mouth is 2 feet in diameter and roughly circular. No sound issues from it, no light can illuminate the inside of it, and any matter that enters it is instantly obliterated.\n\nA successful DC 20 Intelligence (Arcana) check reveals that the mouth contains a _sphere of annihilation_ that can't be controlled or moved. It is otherwise identical to a normal _sphere of annihilation_.\n\nSome versions of the trap include an enchantment placed on the stone face, such that specified creatures feel an overwhelming urge to approach it and crawl inside its mouth. This effect is otherwise like the _sympathy_ aspect of the _antipathy/sympathy_ spell. A successful _dispel magic_ (DC 18) removes this enchantment.",
            "parent": "Rules"
            }
        """

        i = Importer(ImportOptions(update=True, append=False, testrun=False))
        i.import_document(
            json.loads(
                self.test_document_json),
            ImportSpec(
                "test_filename",
                "test_model_class",
                "import_section"))
        i.import_section(
            json.loads(
                self.test_section_json, strict=False),
            ImportSpec(
                "test_filename",
                "test_model_class",
                "import_section"))

    def test_get_section_data(self):
        """Run the API response test for section."""
        response = self.client.get("/sections/?format=json")

        in_section = json.loads(self.test_section_json, strict=False)
        out_section = response.json()['results'][0]

        equal_fields = [
            'name',
            'desc'
        ]

        for field_name in equal_fields:
            self.assertEqual(
                in_section[field_name],
                out_section[field_name],
                f'Mismatched value of: {field_name}')


class FeatsTestCase(APITestCase):
    """Test case for Feat API objects."""

    def setUp(self):
        """Create a document and feat for testing."""
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

        self.test_feat_json = """
            {
            "name": "Grappler",
            "prerequisite": "Strength 13 or higher",
            "desc": "You've developed the skills necessary to hold your own in close-quarters grappling. You gain the following benefits:",
            "effects_desc": [
                "- You have advantage on attack rolls against a creature you are grappling.",
                "- You can use your action to try to pin a creature grappled by you. To do so, make another grapple check. If you succeed, you and the creature are both restrained until the grapple ends."
            ]
            }
        """

        i = Importer(ImportOptions(update=True, append=False, testrun=False))
        i.import_document(
            json.loads(
                self.test_document_json),
            ImportSpec(
                "test_filename",
                "test_model_class",
                "import_feat"))
        i.import_feat(
            json.loads(
                self.test_feat_json),
            ImportSpec(
                "test_filename",
                "test_model_class",
                "import_feat"))

    def test_get_feat_data(self):
        """Run the API response test for feat."""
        response = self.client.get("/feats/?format=json")

        in_feat = json.loads(self.test_feat_json, strict=False)
        out_feat = response.json()['results'][0]

        equal_fields = [
            'name',
            'desc',
            'prerequisite',
            'effects_desc'
        ]

        for field_name in equal_fields:
            self.assertEqual(
                in_feat[field_name],
                out_feat[field_name],
                f'Mismatched value of: {field_name}')


class ConditionsTestCase(APITestCase):
    """Test case for Condition API objects."""

    def setUp(self):
        """Create a document and condition for testing."""
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

        self.test_condition_json = r"""
            {
            "name": "Petrified",
            "desc": "* A petrified creature is transformed, along with any nonmagical object it is wearing or carrying, into a solid inanimate substance (usually stone). Its weight increases by a factor of ten, and it ceases aging.\n* The creature is incapacitated (see the condition), can't move or speak, and is unaware of its surroundings.\n* Attack rolls against the creature have advantage.\n* The creature automatically fails Strength and Dexterity saving throws.\n* The creature has resistance to all damage.\n* The creature is immune to poison and disease, although a poison or disease already in its system is suspended, not neutralized."
            }
        """

        i = Importer(ImportOptions(update=True, append=False, testrun=False))
        i.import_document(
            json.loads(
                self.test_document_json),
            ImportSpec(
                "test_filename",
                "test_model_class",
                "import_condition"))
        i.import_condition(
            json.loads(
                self.test_condition_json),
            ImportSpec(
                "test_filename",
                "test_model_class",
                "import_condition"))

    def test_get_condition_data(self):
        """Run the API response test for condition."""
        response = self.client.get("/conditions/?format=json")

        in_condition = json.loads(self.test_condition_json)
        out_condition = response.json()['results'][0]

        equal_fields = [
            'name',
            'desc'
        ]

        for field_name in equal_fields:
            self.assertEqual(
                in_condition[field_name],
                out_condition[field_name],
                f'Mismatched value of: {field_name}')


class RacesTestCase(APITestCase):
    """Test case for Race API objects."""

    def setUp(self):
        """Create a document and race for testing."""
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

        self.test_race_json = """
            {
            "name": "Dwarf",
            "desc": "## Dwarf Traits\nYour dwarf character has an assortment of inborn abilities, part and parcel of dwarven nature.",
            "asi-desc": "**_Ability Score Increase._** Your Constitution score increases by 2.",
            "asi": [
                {
                    "attributes": [
                        "Constitution"
                    ],
                    "value": 2
                }
            ],
            "age": "**_Age._** Dwarves mature at the same rate as humans, but they're considered young until they reach the age of 50. On average, they live about 350 years.",
            "alignment": "**_Alignment._** Most dwarves are lawful, believing firmly in the benefits of a well-ordered society. They tend toward good as well, with a strong sense of fair play and a belief that everyone deserves to share in the benefits of a just order.",
            "size": "**_Size._** Dwarves stand between 4 and 5 feet tall and average about 150 pounds. Your size is Medium.",
            "speed": {
                "walk": 25
            },
            "speed-desc": "**_Speed._** Your base walking speed is 25 feet. Your speed is not reduced by wearing heavy armor.",
            "languages": "**_Languages._** You can speak, read, and write Common and Dwarvish. Dwarvish is full of hard consonants and guttural sounds, and those characteristics spill over into whatever other language a dwarf might speak.",
            "vision": "**_Darkvision._** Accustomed to life underground, you have superior vision in dark and dim conditions. You can see in dim light within 60 feet of you as if it were bright light, and in darkness as if it were dim light. You can't discern color in darkness, only shades of gray.",
            "traits": "**_Dwarven Resilience._** You have advantage on saving throws against poison, and you have resistance against poison damage.\n\n**_Dwarven Combat Training._** You have proficiency with the battleaxe, handaxe, light hammer, and warhammer.\n\n**_Tool Proficiency._** You gain proficiency with the artisan's tools of your choice: smith's tools, brewer's supplies, or mason's tools.\n\n**_Stonecunning._** Whenever you make an Intelligence (History) check related to the origin of stonework, you are considered proficient in the History skill and add double your proficiency bonus to the check, instead of your normal proficiency bonus.",
            "subtypes": [
                {
                    "name": "Hill Dwarf",
                    "desc": "As a hill dwarf, you have keen senses, deep intuition, and remarkable resilience.",
                    "asi-desc": "**_Ability Score Increase._** Your Wisdom score increases by 1",
                    "asi": [
                        {
                            "attributes": [
                                "Wisdom"
                            ],
                            "value": 1
                        }
                    ],
                    "traits": "**_Dwarven Toughness._** Your hit point maximum increases by 1, and it increases by 1 every time you gain a level."
                }
            ]
        }
        """

        i = Importer(ImportOptions(update=True, append=False, testrun=False))
        i.import_document(
            json.loads(
                self.test_document_json),
            ImportSpec(
                "test_filename",
                "test_model_class",
                "import_race"))
        i.import_race(
            json.loads(
                self.test_race_json, strict=False),
            ImportSpec(
                "test_filename",
                "test_model_class",
                "import_race",
                sub_spec=ImportSpec(
                    "test_filename",
                    Subrace,
                    i.import_subrace)))

    def test_get_race_data(self):
        """Run the API response test for race."""
        response = self.client.get("/races/?format=json")

        in_race = json.loads(self.test_race_json, strict=False)
        out_race = response.json()['results'][0]

        equal_fields = [
            'name',
            'desc',
            'asi',
            'age',
            'alignment',
            'speed',
            'languages',
            'vision',
            'traits'
        ]

        unequal_fields = [
            ('asi-desc', 'asi_desc'),
            ('speed-desc', 'speed_desc'),
        ]

        # TODO: Create tests for subraces.

        for field_name in equal_fields:
            self.assertEqual(
                in_race[field_name],
                out_race[field_name],
                f'Mismatched value of: {field_name}')
        for field_names in unequal_fields:
            self.assertEqual(
                in_race[field_names[0]],
                out_race[field_names[1]],
                f'Mismatched value of unequal field: {field_names}'
            )


class MagicItemsTestCase(APITestCase):
    """Test case for MagicItem API objects."""

    def setUp(self):
        """Create a document and MagicItem for testing."""
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

        self.test_magicitem_json = """
            {
            "name": "Arrow of Slaying",
            "desc": "An _arrow of slaying_ is a magic weapon meant to slay a particular kind of creature. Some are more focused than others; for example, there are both _arrows of dragon slaying_ and _arrows of blue dragon slaying_. If a creature belonging to the type, race, or group associated with an _arrow of slaying_ takes damage from the arrow, the creature must make a DC 17 Constitution saving throw, taking an extra 6d10 piercing damage on a failed save, or half as much extra damage on a successful one.\n\nOnce an _arrow of slaying_ deals its extra damage to a creature, it becomes a nonmagical arrow.\n\nOther types of magic ammunition of this kind exist, such as _bolts of slaying_ meant for a crossbow, though arrows are most common.",
            "type": "Weapon (arrow)",
            "rarity": "very rare"
            }
        """

        i = Importer(ImportOptions(update=True, append=False, testrun=False))
        i.import_document(
            json.loads(
                self.test_document_json),
            ImportSpec(
                "test_filename",
                "test_model_class",
                "import_magicitem"))
        i.import_magic_item(
            json.loads(
                self.test_magicitem_json, strict=False),
            ImportSpec(
                "test_filename",
                "test_model_class",
                "import_magicitem"))

    def test_get_magicitem_data(self):
        """Run the API response test for magicitem."""
        response = self.client.get("/magicitems/?format=json")

        in_magicitem = json.loads(self.test_magicitem_json, strict=False)
        out_magicitem = response.json()['results'][0]

        equal_fields = [
            'name',
            'desc',
            'type',
            'rarity'
        ]

        for field_name in equal_fields:
            self.assertEqual(
                in_magicitem[field_name],
                out_magicitem[field_name],
                f'Mismatched value of: {field_name}')


class WeaponsTestCase(APITestCase):
    """Test case for weapon API objects."""

    def setUp(self):
        """Create a document and weapon for testing."""
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

        self.test_weapon_json = """
        {
        "name": "Crossbow, heavy",
        "category": "Martial Ranged Weapons",
        "cost": "50 gp",
        "damage_dice": "1d10",
        "damage_type": "piercing",
        "weight": "18 lb.",
        "properties": [
            "ammunition (range 100/400)",
            "heavy",
            "loading",
            "two-handed"
        ]
        }
        """

        i = Importer(ImportOptions(update=True, append=False, testrun=False))
        i.import_document(
            json.loads(
                self.test_document_json),
            ImportSpec(
                "test_filename",
                "test_model_class",
                "import_weapon"))
        i.import_weapon(
            json.loads(
                self.test_weapon_json, strict=False),
            ImportSpec(
                "test_filename",
                "test_model_class",
                "import_weapon"))

    def test_get_weapon_data(self):
        """Run the API response test for weapon."""
        response = self.client.get("/weapons/?format=json")

        in_weapon = json.loads(self.test_weapon_json, strict=False)
        out_weapon = response.json()['results'][0]

        equal_fields = [
            'name',
            'category',
            'cost',
            'damage_dice',
            'damage_type',
            'weight',
            'properties'
        ]

        for field_name in equal_fields:
            self.assertEqual(
                in_weapon[field_name],
                out_weapon[field_name],
                f'Mismatched value of: {field_name}')


class ArmorTestCase(APITestCase):
    """Test case for armor API objects."""

    def setUp(self):
        """Create a document and armor for testing."""
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

        self.test_armor_json = """
        {
        "name": "Leather",
        "category": "Light Armor",
        "rarity": "Standard",
        "base_ac": 11,
		"plus_dex_mod": true,
        "cost": "10 gp",
        "weight": "10 lb.",
        "stealth_disadvantage": false
    }
        """

        i = Importer(ImportOptions(update=True, append=False, testrun=False))
        i.import_document(
            json.loads(
                self.test_document_json),
            ImportSpec(
                "test_filename",
                "test_model_class",
                "import_armor"))
        i.import_armor(
            json.loads(
                self.test_armor_json, strict=False),
            ImportSpec(
                "test_filename",
                "test_model_class",
                "import_armor"))

    def test_get_armor_data(self):
        """Run the API response test for armor."""
        response = self.client.get("/armor/?format=json")

        in_armor = json.loads(self.test_armor_json, strict=False)
        out_armor = response.json()['results'][0]

        equal_fields = [
            'name',
            'category',
            'cost',
            'stealth_disadvantage'
        ]

        for field_name in equal_fields:
            self.assertEqual(
                in_armor[field_name],
                out_armor[field_name],
                f'Mismatched value of: {field_name}')
