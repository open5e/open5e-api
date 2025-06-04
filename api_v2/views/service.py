from rest_framework import viewsets
from api_v2 import models, serializers
from .mixins import EagerLoadingMixin


class ServiceViewSet(viewsets.ReadOnlyModelViewSet, EagerLoadingMixin):
  queryset = models.Service.objects.all().order_by('pk')
  serializer_class = serializers.ServiceSerializer

  prefetch_related_fields = ['document']