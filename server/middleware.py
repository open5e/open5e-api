import newrelic.agent

from django.conf import settings

class NewRelicMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        newrelic.agent.add_custom_attribute("referer", request.META.get('HTTP_REFERER', 'unknown'))
        newrelic.agent.add_custom_attribute("userAgent", request.META.get('HTTP_USER_AGENT', 'unknown'))
        newrelic.agent.add_custom_attribute("origin", request.META.get('HTTP_ORIGIN', 'unknown'))
        newrelic.agent.add_custom_attribute("X-Requested-With", request.META.get('HTTP_X_REQUESTED_WITH', 'unknown'))

        response = self.get_response(request)

        return response

class ResponseWarningHeaderMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith('/v1'):
            response_message = "299 Deprecated API: use /v2/ instead. /v1/ will be maintained until 2024-12-31."

            if request.path in ['/v1/search','/v1/search/']:
                response_message = "299 Deprecated API: use /v2/search instead."
 
            response.headers['Warning'] = response_message

        return response

class CacheControlMiddleware:
    """Make cacheable v1 responses actually cacheable at the edge.

    Without a freshness directive Cloudflare will not cache these responses: the
    paths are extensionless, so its default behaviour treats them as dynamic. The
    v1 data only changes on deploy, and deploys purge the zone
    (scripts/clear_cloudflare_cache.sh), so the shared TTL can be generous while
    `max-age` stays short enough to bound staleness in clients we cannot purge.

    The legacy redirects are covered too. A cached 301 is served from the edge, so
    the origin stops seeing that traffic at all - the same benefit the Cloudflare
    redirect rule would have provided, kept here in version control instead.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if self._is_cacheable(request, response):
            response.headers['Cache-Control'] = (
                f'public, max-age={settings.V1_CACHE_MAX_AGE}, '
                f's-maxage={settings.V1_CACHE_SHARED_MAX_AGE}')

        return response

    def _is_cacheable(self, request, response):
        if request.method not in ('GET', 'HEAD'):
            return False

        # Never widen the caching of a response that already asked for something
        # specific, so a view can always opt out by setting its own header.
        if response.has_header('Cache-Control'):
            return False

        # `public` would put per-user content in a shared cache. Nothing in v1 is
        # user-specific today, but a session-bearing response must never be.
        # Cookies live in `response.cookies`, not in a Set-Cookie header.
        if response.cookies:
            return False
        if 'cookie' in response.get('Vary', '').lower():
            return False

        if response.status_code == 200 and request.path.startswith('/v1/'):
            return True

        return (response.status_code == 301
                and getattr(request.resolver_match, 'url_name', None)
                == 'legacy-v1-redirect')
