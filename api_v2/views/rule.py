from rest_framework import viewsets

from django_filters import FilterSet

from api_v2 import models, serializers

from .mixins import EagerLoadingMixin, ExcludeFieldsMixin

class RuleFilterSet(FilterSet):
    class Meta:
        model = models.Rule
        fields = {
            'key': ['in', 'iexact', 'exact' ],
            'name': ['iexact', 'exact', 'icontains'],
            'document__key': ['in','iexact','exact'],
            'document__gamesystem__key': ['in','iexact','exact'],
        }

class RuleViewSet(ExcludeFieldsMixin, viewsets.ReadOnlyModelViewSet):
    queryset = models.Rule.objects.all()
    serializer_class = serializers.RuleSerializer
    filterset_class = RuleFilterSet

class RuleSetFilterSet(FilterSet):
    class Meta:
        model = models.RuleSet
        fields = {
            'key': ['in', 'exact'],
            'name': ['exact', 'contains'],
            'document__key': ['in', 'exact'],
            'document__gamesystem__key': ['in', 'exact'],
        }

class RuleSetViewSet(EagerLoadingMixin, ExcludeFieldsMixin, viewsets.ReadOnlyModelViewSet):
    queryset = models.RuleSet.objects.all()
    serializer_class = serializers.RuleSetSerializer
    filterset_class = RuleSetFilterSet

    select_related_fields = []
    prefetch_related_fields = [
      'document',
      'document__gamesystem',
      'document__publisher',
      'rules',
    ]