from rest_framework import viewsets

from django_filters import FilterSet

from api_v2 import models
from api_v2 import serializers


class AlignmentFilterSet(FilterSet):
    class Meta:
        model = models.Alignment
        fields = {
            'key': ['in', 'iexact', 'exact' ],
            'name': ['iexact', 'exact','contains'],
            'document__key': ['in','iexact','exact'],
            'document__ruleset__key': ['in','iexact','exact'],
        }

class AlignmentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of alignments.
    retrieve: API endpoint for returning a particular alignment.
    """
    queryset = models.Alignment.objects.all().order_by('pk')
    serializer_class = serializers.AlignmentSerializer
    filterset_class = AlignmentFilterSet