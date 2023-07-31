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