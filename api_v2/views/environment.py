""" The view for an Environment. """

from rest_framework import viewsets

from api_v2 import models
from api_v2 import serializers


class EnvironmentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of environments.
    retrieve: API endpoint for returning a particular environment.
    """
    queryset = models.Environment.objects.all().order_by('pk')
    serializer_class = serializers.EnvironmentSerializer



