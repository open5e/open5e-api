"""Viewset and Filterset for the Background Serializers."""
from rest_framework import viewsets

from django_filters import FilterSet

from api_v2 import models, serializers
from .mixins import EagerLoadingMixin, ExcludeFieldsMixin

class BackgroundFilterSet(FilterSet):
    class Meta:
        model = models.Background
        fields = {
            'key': ['in', 'iexact', 'exact'],
            'name': ['iexact', 'exact', 'icontains'],
            'document__key': ['in', 'iexact', 'exact'],
            'document__gamesystem__key': ['in','iexact','exact'],
        }


class BackgroundViewSet(EagerLoadingMixin, ExcludeFieldsMixin, viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of backgrounds.
    retrieve: API endpoint for returning a particular background.
    """
    queryset = models.Background.objects.all().order_by('pk')
    serializer_class = serializers.BackgroundSerializer
    filterset_class = BackgroundFilterSet

    prefetch_related_fields = [
        'crossreferences__reference_content_type',
        'benefits',
        'benefits__crossreferences',
        'document',
        'document__publisher',
        'document__gamesystem'
    ]
