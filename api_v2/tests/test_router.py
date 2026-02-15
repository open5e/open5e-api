
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
    """Verify crossreference field appears on source objects and not on Document/GameSystem/Publisher."""

    def test_item_detail_includes_crossreference_key(self):
        """Objects with desc that are sources (e.g. Item) include crossreference in the response."""
        response = self.client.get("/v2/items/?limit=1&format=json")
        self.assertEqual(response.status_code, 200)
        results = response.json().get("results", [])
        if results:
            item = results[0]
            self.assertIn(
                "crossreference",
                item,
                "Item detail should include crossreference key",
            )
            self.assertIsInstance(item["crossreference"], list)
            for cr in item["crossreference"]:
                self.assertIn("anchor", cr)
                self.assertIn("url", cr)

    def test_document_detail_excludes_crossreference(self):
        """Document responses must not include crossreference."""
        response = self.client.get("/v2/documents/?limit=1&format=json")
        self.assertEqual(response.status_code, 200)
        results = response.json().get("results", [])
        if results:
            self.assertNotIn(
                "crossreference",
                results[0],
                "Document must not include crossreference",
            )

    def test_gamesystem_detail_excludes_crossreference(self):
        """GameSystem responses must not include crossreference."""
        response = self.client.get("/v2/gamesystems/?limit=1&format=json")
        self.assertEqual(response.status_code, 200)
        results = response.json().get("results", [])
        if results:
            self.assertNotIn(
                "crossreference",
                results[0],
                "GameSystem must not include crossreference",
            )

    def test_publisher_detail_excludes_crossreference(self):
        """Publisher responses must not include crossreference."""
        response = self.client.get("/v2/publishers/?limit=1&format=json")
        self.assertEqual(response.status_code, 200)
        results = response.json().get("results", [])
        if results:
            self.assertNotIn(
                "crossreference",
                results[0],
                "Publisher must not include crossreference",
            )
