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
            'document__gamesystem__key': ['in','iexact','exact'],
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

    """
    Set up selects and prefetching nested joins to mitigate N+1 problems
    """
    def get_queryset(self):
        # get 'depth' from query param
        depth = int(self.request.query_params.get('depth', 0)) 
        queryset = RaceViewSet.setup_eager_loading(super().get_queryset(), self.action, depth)
        return queryset

    @staticmethod
    def setup_eager_loading(queryset, action, depth):
        # Apply select_related and prefetch_related based on action and depth
        if action == 'list':
            selects = [
                'document',
                'document__gamesystem',
                'document__publisher',
                'subrace_of'
            ]
            prefetches = ['traits'] # Many-to-many/rvrs relationships to prefetch
            queryset = queryset.select_related(*selects).prefetch_related(*prefetches)
        return queryset