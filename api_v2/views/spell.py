from rest_framework import viewsets

from django_filters import FilterSet

from api_v2 import models
from api_v2 import serializers


class SpellFilterSet(FilterSet):
    class Meta:
        model = models.Spell
        fields = {
            'key': ['in', 'iexact', 'exact'],
            'name': ['iexact', 'exact', 'contains', 'icontains'],
            'document__key': ['in', 'iexact', 'exact'],
            'document__gamesystem__key': ['in', 'iexact', 'exact'],
            'classes__key': ['in', 'iexact', 'exact'],
            'classes__name': ['in'],
            'level': ['exact', 'range', 'gt', 'gte', 'lt', 'lte'],
            'range': ['exact', 'range', 'gt', 'gte', 'lt', 'lte'],
            'school__key': ['exact'],
            'school__name': ['in', 'iexact', 'exact'],
            'duration': ['in', 'iexact', 'exact'],
            'concentration': ['exact'],
            'verbal': ['exact'],
            'somatic': ['exact'],
            'material': ['exact'],
            'material_consumed': ['exact'],
            'casting_time': ['in', 'iexact', 'exact'],
        }

class SpellViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of spells.
    retrieve: API endpoint for returning a particular spell.
    """
    queryset = models.Spell.objects.all().order_by('pk')
    serializer_class = serializers.SpellSerializer
    filterset_class = SpellFilterSet

    def get_queryset(self):
        # Retrieve depth from query params, defaulting to 0 if not provided
        depth = int(self.request.query_params.get('depth', 0))
        return SpellViewSet.setup_eager_loading(super().get_queryset(), depth)

    @staticmethod
    def setup_eager_loading(queryset, depth):
        selects = ['document', 'school', 'document__publisher', 'document__gamesystem']
        prefetches = ['document', 'classes', 'spellcastingoption_set']

        if depth >= 1:
            prefetches = prefetches + ['document__licenses']
        
        if depth >= 2:
            prefetches = prefetches + []

        queryset = queryset.select_related(*selects).prefetch_related(*prefetches)
        return queryset


class SpellSchoolFilterSet(FilterSet):
    class Meta:
        model = models.SpellSchool
        fields = {
            'key': ['in', 'iexact', 'exact' ],
            'name': ['iexact', 'exact','contains'],
            'document__key': ['in','iexact','exact'],
            'document__gamesystem__key': ['in','iexact','exact'],
        }

class SpellSchoolViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.SpellSchool.objects.all().order_by('pk')
    serializer_class = serializers.SpellSchoolSerializer
    filterset_class = SpellSchoolFilterSet