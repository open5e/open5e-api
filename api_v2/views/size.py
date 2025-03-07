from rest_framework import viewsets

from django_filters import FilterSet

from api_v2 import models
from api_v2 import serializers


class SizeFilterSet(FilterSet):
    class Meta:
        model = models.Size
        fields = {
            'key': ['in', 'iexact', 'exact' ],
            'name': ['iexact', 'exact','contains'],
            'document__key': ['in','iexact','exact'],
            'document__gamesystem__key': ['in','iexact','exact'],
        }


class SizeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of damage types.
    retrieve: API endpoint for returning a particular damage type.
    """
    queryset = models.Size.objects.all().order_by('pk')
    serializer_class = serializers.SizeSerializer
    filterset_class = SizeFilterSet

    """
    Set up selects and prefetching nested joins to mitigate N+1 problems
    """
    def get_queryset(self):
        depth = int(self.request.query_params.get('depth', 0)) # get 'depth' from query param
        return SizeViewSet.setup_eager_loading(super().get_queryset(), self.action, depth)

    @staticmethod
    def setup_eager_loading(queryset, action, depth):
        # Apply select_related and prefetch_related based on action and depth
        if action == 'list':
            selects = [
                'document',
                'document__gamesystem',
                'document__publisher',
            ]
            prefetches = [] # Many-to-many/rvrs relationships to prefetch
            queryset = queryset.select_related(*selects).prefetch_related(*prefetches)
        return queryset

