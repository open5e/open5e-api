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
            'document__ruleset__key': ['in','iexact','exact'],
            'subclass_of': ['exact']
        }


class CharacterClassViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of backgrounds.
    retrieve: API endpoint for returning a particular background.
    """
    queryset = models.CharacterClass.objects.all().order_by('pk')
    serializer_class = serializers.CharacterClassSerializer
    filterset_class = CharacterClassFilterSet
