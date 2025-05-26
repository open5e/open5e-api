from rest_framework import viewsets

from django_filters import FilterSet

from api_v2 import models
from api_v2 import serializers

from .mixins import EagerLoadingMixin

class WeaponPropertyViewSet(viewsets.ReadOnlyModelViewSet):
  queryset = models.WeaponProperty.objects.all()
  serializer_class = serializers.WeaponPropertySerializer
  filterset_fields = '__all__'
