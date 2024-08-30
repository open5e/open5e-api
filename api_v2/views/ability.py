from rest_framework import viewsets

from django_filters import FilterSet

from api_v2 import models
from api_v2 import serializers


class AbilityFilterSet(FilterSet):
    class Meta:
        model = models.Ability
        fields = {
            'key': ['in', 'iexact', 'exact' ],
            'name': ['iexact', 'exact','contains'],
            'document__key': ['in','iexact','exact'],
            'document__ruleset__key': ['in','iexact','exact'],
        }

class AbilityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of abilities.
    retrieve: API endpoint for returning a particular ability.
    """
    queryset = models.Ability.objects.all().order_by('pk')
    serializer_class = serializers.AbilitySerializer
    filterset_class = AbilityFilterSet


class SkillFilterSet(FilterSet):
    class Meta:
        models.Skill
        fields = {
            'key': ['in', 'iexact', 'exact' ],
            'name': ['iexact', 'exact','contains'],
            'document__key': ['in','iexact','exact'],
            'document__ruleset__key': ['in','iexact','exact'],
        }


class SkillViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of skills.
    retrieve: API endpoint for returning a particular skill.
    """
    queryset = models.Skill.objects.all().order_by('pk')
    serializer_class = serializers.SkillSerializer
    filterset_class = SkillFilterSet
