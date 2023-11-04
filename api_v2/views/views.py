from django_filters import FilterSet
from django_filters.rest_framework import DjangoFilterBackend
import django_filters
from rest_framework import viewsets

from api_v2 import models
from api_v2 import serializers
from api.schema_generator import CustomSchema



class FeatFilterSet(FilterSet):
    class Meta:
        model = models.Feat
        fields = {
            'key': ['in', 'iexact', 'exact' ],
            'name': ['iexact', 'exact'],
            'document__key': ['in','iexact','exact'],
        }


class FeatViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of feats.
    retrieve: API endpoint for returning a particular feat.
    """
    queryset = models.Feat.objects.all().order_by('pk')
    serializer_class = serializers.FeatSerializer
    filterset_class = FeatFilterSet


class RaceFilterSet(FilterSet):
    class Meta:
        model = models.Race
        fields = {
            'key': ['in', 'iexact', 'exact'],
            'name': ['iexact', 'exact'],
            'document__key': ['in', 'iexact', 'exact'],
        }


class RaceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of races.
    retrieve: API endpoint for returning a particular race.
    """
    queryset = models.Race.objects.all().order_by('pk')
    serializer_class = serializers.RaceSerializer
    filterset_class = RaceFilterSet


