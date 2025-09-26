from rest_framework import routers

class Open5eAPI(routers.APIRootView):
    """
    Welcome to the Open5e API.
    You can review the basic DRF Browseable API here.
    You can review swagger-ui at /schema/swagger-ui/
    You can review redoc at /schema/redoc/
    """

class DocumentedDefaultRouter(routers.DefaultRouter):
    APIRootView = Open5eAPI
