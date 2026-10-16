from django.conf import settings
from django.test import TestCase


class SchemaTest(TestCase):

    def test_version_is_the_release_without_an_api_version(self):
        """/schema/ isn't under /v1/ or /v2/, so it mustn't report the default API version."""
        info = self.client.get('/schema/', {'format': 'json'}).json()['info']

        self.assertEqual(info['version'], settings.VERSION)

    def test_describes_v2_only(self):
        paths = self.client.get('/schema/', {'format': 'json'}).json()['paths']

        self.assertTrue(paths)
        self.assertTrue(all(path.startswith('/v2/') for path in paths))
