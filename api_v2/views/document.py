"""Viewsets for the Document, GameSystem, Publisher, and License Serializers."""
from rest_framework import viewsets
from django_filters import FilterSet, CharFilter
from django.db.models import JSONField

from api_v2 import models
from api_v2 import serializers



class GameSystemViewSet(viewsets.ReadOnlyModelViewSet):
    """"
    list: API Endpoint for returning a set of gamesystems.

    retrieve: API endpoint for return a particular gamesystem.
    """
    queryset = models.GameSystem.objects.all().order_by('pk')
    serializer_class = serializers.GameSystemSerializer


class DocumentFilterSet(FilterSet):
    '''This is the filterset class for Documents.'''
    
    class Meta:
        model = models.Document
        fields = '__all__'
        filter_overrides = {
            JSONField: {
                'filter_class': CharFilter
            }
        }

class DocumentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of documents.
    retrieve: API endpoint for returning a particular document.
    """
    queryset = models.Document.objects.all().order_by('pk')
    serializer_class = serializers.DocumentSerializer
    filterset_class = DocumentFilterSet

    def get_queryset(self):       
        depth = int(self.request.query_params.get('depth', 0)) # get 'depth' from query params
        return DocumentViewSet.setup_eager_loading(super().get_queryset(), self.action, depth)

    @staticmethod
    def setup_eager_loading(queryset, action, depth):
        # Apply select_related and prefetch_related based on action and depth
        if action == 'list':
            selects = ['gamesystem', 'publisher'] #  follows foreign-key relationships
            prefetches = ['licenses']   # Many-to-many/reverse relationships for prefetching
            queryset = queryset.select_related(*selects).prefetch_related(*prefetches)
        return queryset

class PublisherViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of publishers.
    retrieve: API endpoint for returning a particular publisher.
    """
    queryset = models.Publisher.objects.all().order_by('pk')
    serializer_class = serializers.PublisherSerializer
    filterset_fields = '__all__'


class LicenseViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of licenses.
    retrieve: API endpoint for returning a particular license.
    """
    queryset = models.License.objects.all().order_by('pk')
    serializer_class = serializers.LicenseSerializer
    filterset_fields = '__all__'
