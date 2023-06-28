import newrelic.agent

class NewRelicMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        newrelic.agent.add_custom_parameter("Referer", request.META.get('HTTP_REFERER', 'unknown'))
        newrelic.agent.add_custom_parameter("UserAgent", request.META.get('HTTP_USER_AGENT', 'unknown'))
        
        response = self.get_response(request)

        return response