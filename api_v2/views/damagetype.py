from rest_framework import viewsets

from api_v2 import models
from api_v2 import serializers


class DamageTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of damage types.
    retrieve: API endpoint for returning a particular damage type.
    """
    queryset = models.DamageType.objects.all().order_by('pk')
    serializer_class = serializers.DamageTypeSerializer



