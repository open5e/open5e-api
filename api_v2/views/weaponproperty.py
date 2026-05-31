from rest_framework import viewsets

from django_filters import FilterSet

from api_v2 import models, serializers
from .mixins import EagerLoadingMixin, ExcludeFieldsMixin

class WeaponPropertyFilterSet(FilterSet):
    class Meta:
        model = models.WeaponProperty
        fields = {
            'key': ['in', 'iexact', 'exact'],
            'name': ['iexact', 'exact', 'icontains'],
            'type': ['exact', 'isnull'],
            'document__key': ['in', 'iexact', 'exact'],
            'document__gamesystem__key': ['in', 'iexact', 'exact'],
        }

class WeaponPropertyViewSet(EagerLoadingMixin, ExcludeFieldsMixin, viewsets.ReadOnlyModelViewSet):
  queryset = models.WeaponProperty.objects.all()
  serializer_class = serializers.WeaponPropertySerializer
  filterset_class = WeaponPropertyFilterSet

  prefetch_related_fields = ['crossreferences__reference_content_type', 'document']
