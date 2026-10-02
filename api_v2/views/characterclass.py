"""Viewset and Filterset for the CharacterClass Serializers."""
from rest_framework import viewsets

from django_filters import FilterSet, BooleanFilter, ModelChoiceFilter

from api_v2 import models, serializers
from .mixins import EagerLoadingMixin, ExcludeFieldsMixin

class CharacterClassFilterSet(FilterSet):
    """
    Creates: a dropdown list for filtering data.
    Creates: a Django filter that returns a queryset with related
    foreign key objects loaded.
    Ex: Fetch each child class + its parent class in the same query.

    """

    is_subclass = BooleanFilter(field_name='subclass_of', lookup_expr='isnull', exclude=True)

    # Stops Django from creating a query for every parent and instead
    # loads the parent objects together with the CharacterClasses.
    subclass_of = ModelChoiceFilter(queryset = models.CharacterClass.objects.select_related('subclass_of'))

    class Meta:
        model = models.CharacterClass
        fields = {
            'key': ['in', 'iexact', 'exact' ],
            'name': ['iexact', 'exact','contains'],
            'document__key': ['in','iexact','exact'],
            'document__gamesystem__key': ['in','iexact','exact'],
            
        }


class CharacterClassViewSet(ExcludeFieldsMixin, EagerLoadingMixin, viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of classes.
    retrieve: API endpoint for returning a particular class.
    """
    queryset = models.CharacterClass.objects.all().order_by('pk')
    serializer_class = serializers.CharacterClassSerializer
    filterset_class = CharacterClassFilterSet

    select_related_fields = []
    prefetch_related_fields = [
        'crossreferences__reference_content_type',
        'document',
        'features',
        'features__crossreferences',
        'features__feature_items',
        'primary_abilities',
        'saving_throws',
        'subclass_of',
    ]
