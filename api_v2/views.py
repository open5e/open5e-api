import django_filters
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

class DocumentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Document.objects.all()
    serializer_class = serializers.DocumentSerializer


class PublisherViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Publisher.objects.all()
    serializer_class = serializers.PublisherSerializer


class LicenseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.License.objects.all()
    serializer_class = serializers.LicenseSerializer


class WeaponViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Weapon.objects.all()
    serializer_class = serializers.WeaponSerializer


class ArmorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Armor.objects.all()
    serializer_class = serializers.ArmorSerializer