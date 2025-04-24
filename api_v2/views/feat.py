from rest_framework import viewsets
from django_filters import FilterSet

from api_v2 import models
from api_v2 import serializers
from .mixins import EagerLoadingMixin

class FeatFilterSet(FilterSet):
    class Meta:
        model = models.Feat
        fields = {
            'key': ['in', 'iexact', 'exact' ],
            'name': ['iexact', 'exact'],
            'document__key': ['in','iexact','exact'],
            'document__gamesystem__key': ['in','iexact','exact'],
        }


class FeatViewSet(EagerLoadingMixin, viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of feats.
    retrieve: API endpoint for returning a particular feat.
    """
    queryset = models.Feat.objects.all().order_by('pk')
    serializer_class = serializers.FeatSerializer
    filterset_class = FeatFilterSet

    select_related_fields = []
    prefetch_related_fields = ['benefits', 'document']

