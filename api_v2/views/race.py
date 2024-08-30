from rest_framework import viewsets

from django_filters import FilterSet

from api_v2 import models
from api_v2 import serializers


class RaceFilterSet(FilterSet):
    class Meta:
        model = models.Race
        fields = {
            'key': ['in', 'iexact', 'exact'],
            'name': ['iexact', 'exact'],
            'document__key': ['in', 'iexact', 'exact'],
            'document__ruleset__key': ['in','iexact','exact'],
            'subrace_of': ['isnull'],
            'subrace_of__key':['in', 'iexact', 'exact'],
        }


class RaceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of races.
    retrieve: API endpoint for returning a particular race.
    """
    queryset = models.Race.objects.all().order_by('pk')
    serializer_class = serializers.RaceSerializer
    filterset_class = RaceFilterSet
