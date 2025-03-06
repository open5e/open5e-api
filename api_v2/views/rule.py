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

  """
  Set up selects and prefetching nested joins to mitigate N+1 problems
  """
  def get_queryset(self):
      depth = int(self.request.query_params.get('depth', 0)) # get 'depth' from query param
      queryset = RuleSetViewSet.setup_eager_loading(super().get_queryset(), self.action, depth)
      return queryset

  @staticmethod
  def setup_eager_loading(queryset, action, depth):
      # Apply select_related and prefetch_related based on action and depth
      if action == 'list':
          selects = [
              'document',
              'document__gamesystem',
              'document__publisher',
          ]
          prefetches = ['rules'] # Many-to-many/rvrs relationships to prefetch
          queryset = queryset.select_related(*selects).prefetch_related(*prefetches)
      return queryset