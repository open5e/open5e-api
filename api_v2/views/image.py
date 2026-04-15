from rest_framework import viewsets

from django_filters import FilterSet

from api_v2 import models, serializers
from .mixins import EagerLoadingMixin, ExcludeFieldsMixin

class ImageViewSet(ExcludeFieldsMixin, viewsets.ReadOnlyModelViewSet):
    queryset = models.Image.objects.all()
    serializer_class = serializers.ImageSerializer
