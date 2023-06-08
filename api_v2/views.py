from django.shortcuts import render

# Create your views here.
class ItemFilter(django_filters.FilterSet):

    class Meta:
        model = models.Race
        fields = {
            '__all__'
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