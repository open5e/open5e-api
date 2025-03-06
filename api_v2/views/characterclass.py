"""Viewset and Filterset for the CharacterClass Serializers."""
from rest_framework import viewsets

from django_filters import FilterSet
from django_filters import BooleanFilter

from api_v2 import models
from api_v2 import serializers


class CharacterClassFilterSet(FilterSet):
    is_subclass = BooleanFilter(field_name='subclass_of', lookup_expr='isnull', exclude=True)

    class Meta:
        model = models.CharacterClass
        fields = {
            'key': ['in', 'iexact', 'exact' ],
            'name': ['iexact', 'exact','contains'],
            'document__key': ['in','iexact','exact'],
            'document__gamesystem__key': ['in','iexact','exact'],
            'subclass_of': ['exact']
        }


class CharacterClassViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of classes.
    retrieve: API endpoint for returning a particular class.
    """
    queryset = models.CharacterClass.objects.all().order_by('pk')
    serializer_class = serializers.CharacterClassSerializer
    filterset_class = CharacterClassFilterSet

    """
    Set up selects and prefetching nested joins to mitigate N+1 problems
    """
    def get_queryset(self):
        depth = int(self.request.query_params.get('depth', 0)) # get 'depth' from query params
        return CharacterClassViewSet.setup_eager_loading(super().get_queryset(), self.action, depth)

    @staticmethod
    def setup_eager_loading(queryset, action, depth):
        # Apply select_related and prefetch_related based on action and depth
        if action == 'list':
            selects = ['document']
            prefetches = [] # Many-to-many/rvrs relationships to prefetch
            queryset = queryset.select_related(*selects).prefetch_related(*prefetches)
        return queryset
