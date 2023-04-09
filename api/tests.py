"""Test cases for the django API."""

from rest_framework.test import APITestCase

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

        Checks the response for each of the known endpoints. Two results, one for the name, one for the link.
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
                "application/json", "application/x-www-form-urlencoded", "multipart/form-data"])


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
                "application/json", "application/x-www-form-urlencoded", "multipart/form-data"])


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
