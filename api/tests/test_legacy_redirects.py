from django.test import SimpleTestCase
from django.urls import resolve


class LegacyUnversionedRedirectTest(SimpleTestCase):
    """The unversioned endpoints predate versioning and were the v1 shape.

    Clients still calling them should be redirected rather than 404'd.
    """

    def assertRedirectsTo(self, requested, expected):
        response = self.client.get(requested)

        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.headers['Location'], expected)

    def test_monsters_list(self):
        self.assertRedirectsTo('/monsters/', '/v1/monsters/')

    def test_spells_list(self):
        self.assertRedirectsTo('/spells/', '/v1/spells/')

    def test_query_string_is_preserved(self):
        self.assertRedirectsTo('/monsters/?limit=1', '/v1/monsters/?limit=1')

    def test_detail_url(self):
        self.assertRedirectsTo('/monsters/aboleth/', '/v1/monsters/aboleth/')
        self.assertRedirectsTo('/spells/magic-missile/', '/v1/spells/magic-missile/')

    def test_missing_trailing_slash(self):
        """APPEND_SLASH sends these through the redirect on the second hop."""
        self.assertRedirectsTo('/monsters', '/monsters/')

    def test_versioned_urls_are_untouched(self):
        for path in ('/v1/monsters/', '/v1/spells/', '/v2/creatures/'):
            with self.subTest(path=path):
                self.assertNotEqual(
                    resolve(path).url_name, 'legacy-v1-redirect')

    def test_unrelated_legacy_paths_still_404(self):
        self.assertEqual(self.client.get('/feats/').status_code, 404)
