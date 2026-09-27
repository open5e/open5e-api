from django.http import HttpResponse
from django.test import (
    RequestFactory, SimpleTestCase, TestCase, override_settings)

from server.middleware import CacheControlMiddleware


EXPECTED = 'public, max-age=300, s-maxage=86400'


class LegacyRedirectCachingTest(SimpleTestCase):
    """A cached 301 is served from the edge, sparing the origin entirely."""

    def test_redirect_is_cacheable(self):
        response = self.client.get('/monsters/')

        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.headers['Cache-Control'], EXPECTED)

    @override_settings(V1_CACHE_MAX_AGE=60, V1_CACHE_SHARED_MAX_AGE=120)
    def test_durations_are_configurable(self):
        response = self.client.get('/spells/')

        self.assertEqual(
            response.headers['Cache-Control'], 'public, max-age=60, s-maxage=120')

    def test_404_is_not_cacheable(self):
        response = self.client.get('/feats/')

        self.assertEqual(response.status_code, 404)
        self.assertNotIn('Cache-Control', response.headers)


class V1CachingTest(TestCase):
    """v1 endpoints hit the database, so these need a test database."""

    def test_list_is_cacheable(self):
        response = self.client.get('/v1/monsters/', HTTP_ACCEPT='application/json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Cache-Control'], EXPECTED)

    def test_browsable_api_html_is_not_cacheable(self):
        """Cloudflare ignores Vary, so a cached HTML copy could reach JSON clients.

        The browsable API also sets a csrftoken cookie, which must never land in
        a shared cache.
        """
        response = self.client.get('/v1/monsters/', HTTP_ACCEPT='text/html')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers['Content-Type'].startswith('text/html'))
        self.assertNotIn('Cache-Control', response.headers)

    def test_middleware_runs_after_cookies_are_set(self):
        """Regression: the cookie guards are dead if this runs too early.

        Response middleware runs bottom-up, so CacheControlMiddleware has to be
        ahead of the CSRF and session middleware to see their Set-Cookie.
        """
        response = self.client.get('/v1/monsters/', HTTP_ACCEPT='text/html')

        self.assertTrue(response.cookies)
        self.assertNotIn('Cache-Control', response.headers)

    def test_v2_is_untouched(self):
        response = self.client.get('/v2/creatures/', HTTP_ACCEPT='application/json')

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('Cache-Control', response.headers)


class CacheControlGuardTest(SimpleTestCase):
    """The guards that keep `public` from leaking per-user content."""

    def _apply(self, response, path='/v1/monsters/', method='GET'):
        # A bare request, so the guards are exercised without the URL conf.
        request = getattr(RequestFactory(), method.lower())(path)
        return CacheControlMiddleware(lambda _: response)(request)

    def _ok(self):
        return HttpResponse(status=200, content_type='application/json')

    def test_cacheable_baseline(self):
        self.assertEqual(self._apply(self._ok()).headers['Cache-Control'], EXPECTED)

    def test_non_get_is_skipped(self):
        self.assertNotIn(
            'Cache-Control', self._apply(self._ok(), method='POST').headers)

    def test_existing_header_is_not_overwritten(self):
        response = self._ok()
        response.headers['Cache-Control'] = 'no-store'

        self.assertEqual(self._apply(response).headers['Cache-Control'], 'no-store')

    def test_set_cookie_is_skipped(self):
        response = self._ok()
        # Flagged as a real session cookie would be. The guard only looks at
        # whether any cookie is present, so the flags do not affect the test.
        response.set_cookie('sessionid', 'secret', secure=True, httponly=True)

        self.assertNotIn('Cache-Control', self._apply(response).headers)

    def test_non_json_is_skipped(self):
        response = HttpResponse(status=200, content_type='text/html')

        self.assertNotIn('Cache-Control', self._apply(response).headers)

    def test_vary_cookie_is_skipped(self):
        response = self._ok()
        response.headers['Vary'] = 'Accept, Cookie'

        self.assertNotIn('Cache-Control', self._apply(response).headers)
