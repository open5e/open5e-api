from rest_framework import viewsets

from django_filters import FilterSet

from api_v2 import models
from api_v2 import serializers
from .mixins import EagerLoadingMixin

class SizeFilterSet(FilterSet):
    class Meta:
        model = models.Size
        fields = {
            'key': ['in', 'iexact', 'exact' ],
            'name': ['iexact', 'exact','contains'],
            'document__key': ['in','iexact','exact'],
            'document__gamesystem__key': ['in','iexact','exact'],
        }


class SizeViewSet(EagerLoadingMixin, viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of damage types.
    retrieve: API endpoint for returning a particular damage type.
    """
    queryset = models.Size.objects.all().order_by('pk')
    serializer_class = serializers.SizeSerializer
    filterset_class = SizeFilterSet

    select_related_fields = []
    prefetch_related_fields = ['document__gamesystem', 'document__publisher']

