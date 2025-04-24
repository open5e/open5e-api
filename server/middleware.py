import newrelic.agent

class NewRelicMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        newrelic.agent.add_custom_parameter("referer", request.META.get('HTTP_REFERER', 'unknown'))
        newrelic.agent.add_custom_parameter("userAgent", request.META.get('HTTP_USER_AGENT', 'unknown'))
        newrelic.agent.add_custom_parameter("origin", request.META.get('HTTP_ORIGIN', 'unknown'))
        newrelic.agent.add_custom_parameter("X-Requested-With", request.META.get('HTTP_X_REQUESTED_WITH', 'unknown'))

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