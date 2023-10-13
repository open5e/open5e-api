"""Test cases for the django API."""
import json

from pathlib import Path

from rest_framework.test import APITestCase

from api.management.commands.importer import Importer
from api.management.commands.importer import ImportSpec
from api.management.commands.importer import ImportOptions

from django.template.defaultfilters import slugify

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
        self.assertContains(response, 'spelllist', count=2)
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

