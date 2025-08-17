from rest_framework import viewsets

from django_filters import FilterSet

from api_v2 import models
from api_v2 import serializers

from .mixins import EagerLoadingMixin

class RuleFilterSet(FilterSet):
    class Meta:
        model = models.Rule
        fields = {
            'key': ['in', 'iexact', 'exact' ],
            'name': ['iexact', 'exact', 'icontains'],
            'document__key': ['in','iexact','exact'],
            'document__gamesystem__key': ['in','iexact','exact'],
        }

class RuleViewSet(viewsets.ReadOnlyModelViewSet):
  queryset = models.Rule.objects.all()
  serializer_class = serializers.RuleSerializer
  filterset_class = RuleFilterSet


class RuleSetViewSet(EagerLoadingMixin, viewsets.ReadOnlyModelViewSet):
  queryset = models.RuleSet.objects.all()
  serializer_class = serializers.RuleSetSerializer

  select_related_fields = []
  prefetch_related_fields = [
    'document',
    'document__gamesystem',
    'document__publisher',
    'rules',
  ]