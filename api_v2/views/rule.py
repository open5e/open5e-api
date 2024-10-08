from rest_framework import viewsets

from django_filters import FilterSet

from api_v2 import models
from api_v2 import serializers

class RuleViewSet(viewsets.ReadOnlyModelViewSet):
  queryset = models.Rule.objects.all()
  serializer_class = serializers.RuleSerializer

class RuleSetViewSet(viewsets.ReadOnlyModelViewSet):
  queryset = models.RuleSet.objects.all()
  serializer_class = serializers.RuleSetSerializer