"""Viewset and Filterset for the Background Serializers."""
from rest_framework import viewsets

from django_filters import FilterSet

from api_v2 import models
from api_v2 import serializers


class BackgroundFilterSet(FilterSet):
    class Meta:
        model = models.Background
        fields = {
            'key': ['in', 'iexact', 'exact'],
            'name': ['iexact', 'exact'],
            'document__key': ['in', 'iexact', 'exact'],
            'document__gamesystem__key': ['in','iexact','exact'],
        }


class BackgroundViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of backgrounds.
    retrieve: API endpoint for returning a particular background.
    """
    queryset = models.Background.objects.all().order_by('pk')
    serializer_class = serializers.BackgroundSerializer
    filterset_class = BackgroundFilterSet

    def get_queryset(self):
        depth = int(self.request.query_params.get('depth', 0)) # get 'depth' from query params
        return BackgroundViewSet.setup_eager_loading(super().get_queryset(), self.action, depth)

    @staticmethod
    def setup_eager_loading(queryset, action, depth):
        # Apply select_related and prefetch_related based on action and depth
        if action == 'list':
            selects = []
            prefetches = ['benefits'] # Many-to-many/rvrs relationships to prefetch
            queryset = queryset.select_related(*selects).prefetch_related(*prefetches)
        return queryset