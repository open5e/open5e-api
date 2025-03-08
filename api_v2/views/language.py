from rest_framework import viewsets

from django_filters import FilterSet

from api_v2 import models
from api_v2 import serializers

from .mixins import EagerLoadingMixin


class LanguageFilterSet(FilterSet):
    class Meta:
        model = models.Language
        fields = {
            'key': ['in', 'iexact', 'exact' ],
            'name': ['iexact', 'exact'],
            'document__key': ['in','iexact','exact'],
            'document__gamesystem__key': ['in','iexact','exact'],
            'is_exotic': ['exact'],
            'is_secret': ['exact']
        }


class LanguageViewSet(EagerLoadingMixin, viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of feats.
    retrieve: API endpoint for returning a particular feat.
    """
    queryset = models.Language.objects.all().order_by('pk')
    serializer_class = serializers.LanguageSerializer
    filterset_class = LanguageFilterSet

    select_related_fields = []
    prefetch_related_fields = [
        'document',
        'document__gamesystem',
        'document__publisher',
    ]