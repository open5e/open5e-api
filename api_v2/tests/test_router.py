
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
        self.assertContains(response, 'rulesets', count=2)
        self.assertContains(response, 'items', count=4) #include itemsets
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
