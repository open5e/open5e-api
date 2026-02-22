from rest_framework import viewsets

from django_filters import FilterSet

from api_v2 import models
from api_v2 import serializers

from .mixins import EagerLoadingMixin

class SpeciesFilterSet(FilterSet):
    class Meta:
        model = models.Species
        fields = {
            'key': ['in', 'iexact', 'exact'],
            'name': ['iexact', 'exact', 'icontains'],
            'document__key': ['in', 'iexact', 'exact'],
            'document__gamesystem__key': ['in','iexact','exact'],
            'subspecies_of': ['isnull'],
            'subspecies_of__key':['in', 'iexact', 'exact'],
        }


class SpeciesViewSet(EagerLoadingMixin, viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of species.
    retrieve: API endpoint for returning a particular species.
    """
    queryset = models.Species.objects.all().order_by('pk')
    serializer_class = serializers.SpeciesSerializer
    filterset_class = SpeciesFilterSet

    select_related_fields = []
    prefetch_related_fields = [
        'crossreferences__reference_content_type',
        'document',
        'document__gamesystem',
        'traits',
        'subspecies_of'
    ]