from rest_framework import viewsets

from django_filters import FilterSet
from django_filters import BooleanFilter


from api_v2 import models
from api_v2 import serializers

class ItemFilterSet(FilterSet):
    is_magic_item = BooleanFilter(field_name='rarity', lookup_expr='isnull', exclude=True)

    class Meta:
        model = models.Item
        fields = {
            'key': ['in', 'iexact', 'exact'],
            'name': ['iexact', 'exact', 'icontains'],
            'desc': ['icontains'],
            'cost': ['exact', 'range', 'gt', 'gte', 'lt', 'lte'],
            'weight': ['exact', 'range', 'gt', 'gte', 'lt', 'lte'],
            'rarity': ['exact', 'in'],
            'requires_attunement': ['exact'],
            'category': ['in', 'exact'],
            'document__key': ['in','iexact','exact'],
            'document__gamesystem__key': ['in','iexact','exact'],
        }


class ItemViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of items.

    retrieve: API endpoint for returning a particular item.
    """
    queryset = models.Item.objects.all().order_by('pk')
    serializer_class = serializers.ItemSerializer
    filterset_class = ItemFilterSet

    def get_queryset(self):
        depth = int(self.request.query_params.get('depth', 0))
        queryset = ItemViewSet.setup_eager_loading(super().get_queryset(), self.action, depth)
        return queryset

    # Eagerly load nested resources to address N+1 problems
    @staticmethod
    def setup_eager_loading(queryset, action, depth):
        if action == 'list':
            selects = ['armor', 'weapon']
            # Prefetch many-to-many and reverse ForeignKey relations
            prefetches = [
                'category', 'document', 'document__licenses',
                'damage_immunities', 'damage_resistances', 
                'damage_vulnerabilities', 'rarity'
            ]
            queryset = queryset.select_related(*selects).prefetch_related(*prefetches)
        return queryset

class ItemRarityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of item rarities.

    retrieve: API endpoint for returning a particular item rarity.
    """
    queryset = models.ItemRarity.objects.all().order_by('pk')
    serializer_class = serializers.ItemRaritySerializer



class ItemSetFilterSet(FilterSet):

    class Meta:
        model = models.ItemSet
        fields = {
            'key': ['in', 'iexact', 'exact' ],
            'name': ['iexact', 'exact'],
            'document__key': ['in','iexact','exact'],
            'document__gamesystem__key': ['in','iexact','exact'],
        }


class ItemSetViewSet(viewsets.ReadOnlyModelViewSet):
    """"
    list: API Endpoint for returning a set of itemsets.

    retrieve: API endpoint for return a particular itemset.
    """
    queryset = models.ItemSet.objects.all().order_by('pk')
    serializer_class = serializers.ItemSetSerializer
    filterset_class = ItemSetFilterSet


class ItemCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """"
    list: API Endpoint for returning a set of item categories.

    retrieve: API endpoint for return a particular item categories.
    """
    queryset = models.ItemCategory.objects.all().order_by('pk')
    serializer_class = serializers.ItemCategorySerializer


class WeaponFilterSet(FilterSet):

    class Meta:
        model = models.Weapon
        fields = {
            'key': ['in', 'iexact', 'exact' ],
            'name': ['iexact', 'exact'],
            'document__key': ['in','iexact','exact'],
            'document__gamesystem__key': ['in','iexact','exact'],
            'damage_dice': ['in','iexact','exact'],
            'versatile_dice': ['in','iexact','exact'],
            'reach': ['exact','lt','lte','gt','gte'],
            'range': ['exact','lt','lte','gt','gte'],
            'long_range': ['exact','lt','lte','gt','gte'],
            'is_finesse': ['exact'],
            'is_thrown': ['exact'],
            'is_two_handed': ['exact'],
            'requires_ammunition': ['exact'],
            'requires_loading': ['exact'],
            'is_heavy': ['exact'],
            'is_light': ['exact'],
            'is_lance': ['exact'],
            'is_net': ['exact'],
            'is_simple': ['exact'],
            'is_improvised': ['exact']
            }


class WeaponViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of weapons.
    retrieve: API endpoint for returning a particular weapon.
    """
    queryset = models.Weapon.objects.all().order_by('pk')
    serializer_class = serializers.WeaponSerializer
    filterset_class = WeaponFilterSet


class ArmorFilterSet(FilterSet):

    class Meta:
        model = models.Armor
        fields = {
            'key': ['in', 'iexact', 'exact' ],
            'name': ['iexact', 'exact'],
            'document__key': ['in','iexact','exact'],
            'document__gamesystem__key': ['in','iexact','exact'],
            'grants_stealth_disadvantage': ['exact'],
            'strength_score_required': ['exact','lt','lte','gt','gte'],
            'ac_base': ['exact','lt','lte','gt','gte'],
            'ac_add_dexmod': ['exact'],
            'ac_cap_dexmod': ['exact'],

        }


class ArmorViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of armor.
    retrieve: API endpoint for returning a particular armor.
    """
    queryset = models.Armor.objects.all().order_by('pk')
    serializer_class = serializers.ArmorSerializer
    filterset_class = ArmorFilterSet
