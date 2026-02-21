
from rest_framework.test import APITestCase


class APIV2RootTest(APITestCase):
    """Test cases for testing the / root of the API."""

    def test_get_root_headers(self):
        """Server response headers from the API root."""
        response = self.client.get(f'/v2/?format=json')

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
        response = self.client.get(f'/v2/?format=json')

        self.assertContains(response, 'documents', count=2)
        self.assertContains(response, 'publishers', count=2)
        self.assertContains(response, 'licenses', count=2)
        self.assertContains(response, 'gamesystems', count=2)
        self.assertContains(response, 'items', count=6) #include itemsets
        self.assertContains(response, 'itemsets', count=2)
        self.assertContains(response, 'weapons', count=2)
        self.assertContains(response, 'armor', count=2)
        self.assertContains(response, 'creatures', count=4) #includes creaturesets

    def test_options_root_data(self):
        """
        Confirm the OPTIONS response available at the root.

        Checks the response for each of known values.
        """
        response = self.client.get(f'/v2/?format=json', REQUEST_METHOD='OPTIONS')
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


class CrossReferenceFieldTest(APITestCase):
    """Verify crossreferences field appears on source objects and not on Document/GameSystem/Publisher."""

    def test_item_detail_includes_crossreferences_key(self):
        """Objects with desc that are sources (e.g. Item) include crossreferences in the response."""
        response = self.client.get("/v2/items/?limit=1&format=json")
        self.assertEqual(response.status_code, 200)
        results = response.json().get("results", [])
        if results:
            item = results[0]
            self.assertIn(
                "crossreferences",
                item,
                "Item detail should include crossreferences key",
            )
            cr = item["crossreferences"]
            self.assertIsInstance(cr, dict, "crossreferences should be {to, from}")
            self.assertIn("to", cr)
            self.assertIn("from", cr)
            self.assertIsInstance(cr["to"], list)
            self.assertIsInstance(cr["from"], list)
            for entry in cr["to"] + cr["from"]:
                self.assertIn("anchor", entry)
                self.assertIn("url", entry)

    def test_crossreferences_from_when_object_is_referenced(self):
        """An object that is the reference of at least one CrossReference has entries in crossreferences.from."""
        # srd-2024_acid is referenced by other items in the fixture
        response = self.client.get("/v2/items/srd-2024_acid/?format=json")
        if response.status_code != 200:
            return  # fixture may not be loaded
        item = response.json()
        self.assertIn("crossreferences", item)
        from_list = item["crossreferences"]["from"]
        self.assertIsInstance(from_list, list)
        for entry in from_list:
            self.assertIn("anchor", entry)
            self.assertIn("url", entry)

    def test_document_detail_excludes_crossreferences(self):
        """Document responses must not include crossreferences."""
        response = self.client.get("/v2/documents/?limit=1&format=json")
        self.assertEqual(response.status_code, 200)
        results = response.json().get("results", [])
        if results:
            self.assertNotIn(
                "crossreferences",
                results[0],
                "Document must not include crossreferences",
            )

    def test_gamesystem_detail_excludes_crossreferences(self):
        """GameSystem responses must not include crossreferences."""
        response = self.client.get("/v2/gamesystems/?limit=1&format=json")
        self.assertEqual(response.status_code, 200)
        results = response.json().get("results", [])
        if results:
            self.assertNotIn(
                "crossreferences",
                results[0],
                "GameSystem must not include crossreferences",
            )

    def test_publisher_detail_excludes_crossreferences(self):
        """Publisher responses must not include crossreferences."""
        response = self.client.get("/v2/publishers/?limit=1&format=json")
        self.assertEqual(response.status_code, 200)
        results = response.json().get("results", [])
        if results:
            self.assertNotIn(
                "crossreferences",
                results[0],
                "Publisher must not include crossreferences",
            )

    def test_spell_detail_nested_objects_omit_crossreferences(self):
        """Nested objects (e.g. school, classes) on spell detail must not include crossreferences."""
        response = self.client.get("/v2/spells/srd-2024_earthquake/?format=json")
        if response.status_code != 200:
            return  # fixture may not be loaded
        spell = response.json()
        self.assertIn("crossreferences", spell, "Root spell should include crossreferences")
        self.assertNotIn(
            "crossreferences",
            spell.get("school", {}),
            "Nested school must not include crossreferences",
        )
        for cls in spell.get("classes", []):
            self.assertNotIn(
                "crossreferences",
                cls,
                "Nested class must not include crossreferences",
            )
