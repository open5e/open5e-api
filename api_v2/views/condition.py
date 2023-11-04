from rest_framework import viewsets

from api_v2 import models
from api_v2 import serializers


class ConditionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of conditions.
    retrieve: API endpoint for returning a particular condition.
    """
    queryset = models.Condition.objects.all().order_by('pk')
    serializer_class = serializers.ConditionSerializer



