import json

from pathlib import Path

from rest_framework.test import APITestCase

from api.management.commands.importer import Importer
from api.management.commands.importer import ImportSpec
from api.management.commands.importer import ImportOptions


# Create your tests here.

class APIRootTest(APITestCase):
    def test_get_root_headers(self):
        response = self.client.get(f'/?format=json')
        # Assert basic headers
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['allow'], 'GET, HEAD, OPTIONS')
        self.assertEqual(response.headers['content-type'], 'application/json')
        self.assertEqual(response.headers['X-Frame-Options'], 'DENY')
        self.assertEqual(response.headers['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(response.headers['Referrer-Policy'], 'same-origin')

    def test_get_root_list(self):
        response = self.client.get(f'/?format=json')
        # Check the response for each of the known endpoints. Two results, one
        # for the name, one for the link.
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
        # Testing the actual content of the response data.
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
        self.assertContains(response, 'count', count=1)
        self.assertContains(response, 'next', count=1)
        self.assertContains(response, 'previous', count=1)
        self.assertContains(response, 'results', count=1)

        # Confirm the values appear as expected.
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


class MonstersTestCase(APITestCase):
    """Test case for the monster API endpoint."""

    def setUp(self):
        """Create a test document and monster."""
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
