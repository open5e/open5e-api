from rest_framework import viewsets

from django_filters import FilterSet

from api_v2 import models
from api_v2 import serializers


class SpellFilterSet(FilterSet):
    class Meta:
        model = models.Spell
        fields = {
            'key': ['in', 'iexact', 'exact' ],
            'name': ['iexact', 'exact','contains'],
            'document__key': ['in','iexact','exact'],
        }


class SpellViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of spells.
    retrieve: API endpoint for returning a particular spell.
    """
    queryset = models.Spell.objects.all().order_by('pk')
    serializer_class = serializers.SpellSerializer
    filterset_class = SpellFilterSet


class SpellSetViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of spellsets.
    retrieve: API endpoint for returning a particular spellset.
    """
    queryset = models.SpellSet.objects.all().order_by('pk')
    serializer_class = serializers.SpellSetSerializer

