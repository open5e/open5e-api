from rest_framework import viewsets

from django_filters import FilterSet

from api_v2 import models
from api_v2 import serializers
from .mixins import EagerLoadingMixin

class ConditionFilterSet(FilterSet):
    class Meta:
        model = models.Condition
        fields = {
            'key': ['in', 'iexact', 'exact' ],
            'name': ['iexact', 'exact','contains'],
            'document__key': ['in','iexact','exact'],
            'document__gamesystem__key': ['in','iexact','exact'],
        }


class ConditionViewSet(EagerLoadingMixin, viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of conditions.
    retrieve: API endpoint for returning a particular condition.
    """
    queryset = models.Condition.objects.all().order_by('pk')
    serializer_class = serializers.ConditionSerializer
    filterset_class = ConditionFilterSet

    select_related_fields = []
    prefetch_related_fields = ['document__gamesystem',
                                'icon']


class ConditionConceptFilterSet(FilterSet):
    class Meta:
        model = models.ConditionConcept
        fields = {
            'key': ['in', 'iexact', 'exact'],
            'name': ['iexact', 'exact', 'contains'],
            'conditions__document__key': ['in', 'iexact', 'exact'],
            'conditions__document__gamesystem__key': ['in', 'iexact', 'exact'],
        }


class ConditionConceptViewSet(EagerLoadingMixin, viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of condition concepts that aggregate equivalent conditions across game systems.
    retrieve: API endpoint for returning a particular condition concept.
    
    Condition concepts represent the same conceptual condition (e.g., "Invisible") 
    across different game systems, providing a unified view with links to the 
    system-specific implementations.
    """
    queryset = models.ConditionConcept.objects.all().order_by('name')
    serializer_class = serializers.ConditionConceptSerializer
    filterset_class = ConditionConceptFilterSet

    select_related_fields = []
    prefetch_related_fields = [
        'conditions__document__gamesystem',
        'conditions__document__publisher',
        'conditions__icon'
    ]