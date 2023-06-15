import django_filters
from rest_framework import viewsets

from api_v2 import models
from api_v2 import serializers
from api.schema_generator import CustomSchema
# Create your views here.
class ItemFilter(django_filters.FilterSet):

    class Meta:
        model = models.Item
        fields = {
            'name'
        }

class ItemViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of items.
    """
    schema = CustomSchema(
        summary={
            '/items/': 'List Items',
        },
        tags=['Items']
    )
    queryset = models.Item.objects.all()
    serializer_class = serializers.ItemSerializer
    filterset_class = ItemFilter

class DocumentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Document.objects.all()
    serializer_class = serializers.DocumentSerializer
