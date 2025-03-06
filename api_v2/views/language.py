from rest_framework import viewsets

from django_filters import FilterSet

from api_v2 import models
from api_v2 import serializers


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


class LanguageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of feats.
    retrieve: API endpoint for returning a particular feat.
    """
    queryset = models.Language.objects.all().order_by('pk')
    serializer_class = serializers.LanguageSerializer
    filterset_class = LanguageFilterSet

    """
    Set up selects and prefetching nested joins to mitigate N+1 problems
    """
    def get_queryset(self):
        # get 'depth' from query param
        depth = int(self.request.query_params.get('depth', 0)) 
        queryset = LanguageViewSet.setup_eager_loading(super().get_queryset(), self.action, depth)
        return queryset

    @staticmethod
    def setup_eager_loading(queryset, action, depth):
        # Apply select_related and prefetch_related based on action and depth
        if action == 'list':
            selects = ['document', 'document__gamesystem', 'document__publisher']
            prefetches = [] # Many-to-many/rvrs relationships to prefetch
            queryset = queryset.select_related(*selects).prefetch_related(*prefetches)
        return queryset