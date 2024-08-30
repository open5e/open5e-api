""" The view for an Environment. """

from rest_framework import viewsets

from django_filters import FilterSet

from api_v2 import models
from api_v2 import serializers


class EnvironmentFilterSet(FilterSet):
    class Meta:
        model = models.Environment
        fields = {
            'key': ['in', 'iexact', 'exact' ],
            'name': ['iexact', 'exact','contains'],
            'document__key': ['in','iexact','exact'],
            'document__ruleset__key': ['in','iexact','exact'],
        }



class EnvironmentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of environments.
    retrieve: API endpoint for returning a particular environment.
    """
    queryset = models.Environment.objects.all().order_by('pk')
    serializer_class = serializers.EnvironmentSerializer
    filterset_class = EnvironmentFilterSet
