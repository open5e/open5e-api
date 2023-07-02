from django_filters import FilterSet
from django_filters import BooleanFilter
from django_filters.rest_framework import DjangoFilterBackend
import django_filters
from rest_framework import viewsets

from api_v2 import models
from api_v2 import serializers
from api.schema_generator import CustomSchema

class ItemFilterSet(FilterSet):
    is_magic_item = BooleanFilter(field_name='rarity', lookup_expr='isnull', exclude=True)

    class Meta:
        model = models.Item
        fields = {
            'key': ['in', 'iexact', 'exact' ],
            'name': ['iexact', 'exact'],
            'desc': ['icontains'],
            'cost': ['exact', 'range', 'gt', 'gte', 'lt', 'lte'],
            'weight': ['exact', 'range', 'gt', 'gte', 'lt', 'lte'],
            'rarity': ['exact', 'in', ],
            'requires_attunement': ['exact'],
        }
# Create your views here.

class ItemViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of items.

    retrieve: API endpoint for returning a particular item.
    """
    queryset = models.Item.objects.all().order_by('-pk')
    serializer_class = serializers.ItemSerializer
    filterset_class = ItemFilterSet

class ItemSetViewSet(viewsets.ReadOnlyModelViewSet):
    """"
    list: API Endpoint for returning a set of itemsets.

    retrieve: API endpoint for return a particular itemset.
    """
    queryset = models.ItemSet.objects.all().order_by('-pk')
    serializer_class = serializers.ItemSetSerializer


class DocumentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of documents.
    retrieve: API endpoint for returning a particular document.
    """
    queryset = models.Document.objects.all().order_by('-pk')
    serializer_class = serializers.DocumentSerializerFull
    filterset_fields = '__all__'


class PublisherViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of publishers.
    retrieve: API endpoint for returning a particular publisher.
    """
    queryset = models.Publisher.objects.all().order_by('-pk')
    serializer_class = serializers.PublisherSerializer
    filterset_fields = '__all__'


class LicenseViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of licenses.
    retrieve: API endpoint for returning a particular license.
    """
    queryset = models.License.objects.all().order_by('-pk')
    serializer_class = serializers.LicenseSerializer
    filterset_fields = '__all__'


class WeaponViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of weapons.
    retrieve: API endpoint for returning a particular weapon.
    """
    queryset = models.Weapon.objects.all().order_by('-pk')
    serializer_class = serializers.WeaponSerializerFull
    filterset_fields = '__all__'


class ArmorViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of armor.
    retrieve: API endpoint for returning a particular armor.
    """
    queryset = models.Armor.objects.all().order_by('-pk')
    serializer_class = serializers.ArmorSerializerFull
    filterset_fields = '__all__'
