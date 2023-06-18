from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets

from api_v2 import models
from api_v2 import serializers
from api.schema_generator import CustomSchema
# Create your views here.


class ItemViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of items.
    """
    queryset = models.Item.objects.all().order_by('-pk')
    serializer_class = serializers.ItemSerializer
    filterset_fields = '__all__'


class DocumentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Document.objects.all().order_by('-pk')
    serializer_class = serializers.DocumentSerializer
    filterset_fields = '__all__'


class PublisherViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Publisher.objects.all().order_by('-pk')
    serializer_class = serializers.PublisherSerializer
    filterset_fields = '__all__'


class LicenseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.License.objects.all().order_by('-pk')
    serializer_class = serializers.LicenseSerializer
    filterset_fields = '__all__'


class WeaponViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Weapon.objects.all().order_by('-pk')
    serializer_class = serializers.WeaponSerializer
    filterset_fields = '__all__'


class ArmorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Armor.objects.all().order_by('-pk')
    serializer_class = serializers.ArmorSerializer
    filterset_fields = '__all__'
