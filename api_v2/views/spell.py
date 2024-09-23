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
            'document__ruleset__key': ['in', 'iexact', 'exact'],
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

