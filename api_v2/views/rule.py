from rest_framework import viewsets

from django_filters import FilterSet

from api_v2 import models
from api_v2 import serializers

class RuleSectionViewSet(viewsets.ReadOnlyModelViewSet):
  queryset = models.Rule.objects.all()
  serializer_class = serializers.RuleSerializer

class RuleGroupViewSet(viewsets.ReadOnlyModelViewSet):
  queryset = models.RuleGroup.objects.all()
  serializer_class = serializers.RuleGroupSerializer