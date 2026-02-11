from rest_framework import viewsets

from django_filters import FilterSet

from api_v2 import models, serializers
from .mixins import ExcludeFieldsMixin


class DamageTypeFilterSet(FilterSet):
    class Meta:
        model = models.DamageType
        fields = {
            'key': ['in', 'iexact', 'exact' ],
            'name': ['iexact', 'exact','contains'],
            'document__key': ['in','iexact','exact'],
            'document__gamesystem__key': ['in','iexact','exact'],
        }


class DamageTypeViewSet(ExcludeFieldsMixin, viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of damage types.
    retrieve: API endpoint for returning a particular damage type.
    """
    queryset = models.DamageType.objects.all().order_by('pk')
    serializer_class = serializers.DamageTypeSerializer
    filterset_class = DamageTypeFilterSet
