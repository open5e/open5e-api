from rest_framework import viewsets

from api_v2 import models
from api_v2 import serializers


class AlignmentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of alignments.
    retrieve: API endpoint for returning a particular alignment.
    """
    queryset = models.Alignment.objects.all().order_by('pk')
    serializer_class = serializers.AlignmentSerializer



