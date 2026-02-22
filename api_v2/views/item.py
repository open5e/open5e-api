from rest_framework import viewsets
from django_filters import FilterSet, BooleanFilter

from api_v2 import models, serializers
from .mixins import EagerLoadingMixin

class ItemFilterSet(FilterSet):
    ''' Filter set for the Item model. Used in the ItemViewSet below '''

    is_magic_item = BooleanFilter(
        label='Magic Items',
        field_name='rarity',
        lookup_expr='isnull',
        exclude=True
    )

    is_weapon = BooleanFilter(
        label='Weapons',
        field_name='weapon',
        lookup_expr='isnull',
        exclude=True
    )

    is_armor = BooleanFilter(
        label='Armor',
        field_name='armor',
        lookup_expr='isnull',
        exclude=True
    )
    
    # Weapon property filter factory method
    def weapon_property_filter(property_name):
        return lambda queryset, name, value: (
            queryset.filter(weapon__properties__property__name__iexact=property_name)
        )

    # Filters for weapon properties (using the factory method defined above)
    is_light = BooleanFilter(label='Light Weapons', method=weapon_property_filter('light'))
    is_versatile = BooleanFilter(label='Versatile Weapons', method=weapon_property_filter('versatile'))
    is_thrown = BooleanFilter(label='Thrown Weapons', method=weapon_property_filter('thrown'))
    is_finesse = BooleanFilter(label='Finesse Weapons', method = weapon_property_filter('finesse'))
    is_two_handed = BooleanFilter(label='Two-handed Weapons', method=weapon_property_filter('two-handed'))

    class Meta:
        model = models.Item
        fields = {
            'key': ['in', 'iexact'],
            'name': ['iexact', 'icontains'],
            'desc': ['icontains'],
            'cost': ['exact', 'range', 'gt', 'gte', 'lt', 'lte'],
            'weight': ['exact', 'range', 'gt', 'gte', 'lt', 'lte'],
            'rarity': ['exact', 'in'],
            'requires_attunement': ['iexact'],
            'category': ['in', 'exact'],
            'document': ['in', 'exact'],
            'document__key': ['in','iexact'],
            'document__gamesystem__key': ['in','iexact'],
        }

# used in ItemViewSet and MagicItemViewSet - factored out for DRYness
item_prefetch_fields = [
    'crossreferences__reference_content_type',
    'armor',
    'category',
    'damage_immunities',
    'damage_resistances',
    'damage_vulnerabilities',
    'document',
    'weapon__properties',
    'weapon__damage_type',
    'weapon__document',
    'weapon__properties__property',
    'rarity',
    'size',
]

class ItemViewSet(EagerLoadingMixin, viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of items.

    retrieve: API endpoint for returning a particular item.
    """
    queryset = models.Item.objects.all().order_by('pk')
    serializer_class = serializers.ItemSerializer
    filterset_class = ItemFilterSet

    select_related_fields = ['armor', 'weapon']
    prefetch_related_fields = item_prefetch_fields

class MagicItemViewSet(EagerLoadingMixin, viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of magic items.

    retrieve: API endpoint for returning a particular magic item.
    """
    queryset = models.Item.objects.filter(rarity__isnull=False).order_by('pk')
    serializer_class = serializers.ItemSerializer
    filterset_class = ItemFilterSet
    
    select_related_fields = ['armor', 'weapon']
    prefetch_related_fields = item_prefetch_fields

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


class ItemSetViewSet(EagerLoadingMixin, viewsets.ReadOnlyModelViewSet):
    """"
    list: API Endpoint for returning a set of itemsets.

    retrieve: API endpoint for return a particular itemset.
    """
    queryset = models.ItemSet.objects.all().order_by('pk')
    serializer_class = serializers.ItemSetSerializer
    filterset_class = ItemSetFilterSet

    prefetch_related_fields = [
        'crossreferences__reference_content_type',
        'items',
        'items__document',
        'items__damage_resistances',
        'items__damage_immunities',
        'items__damage_vulnerabilities',
        'items__armor',
        'items__category',
        'items__weapon',
        'items__weapon__document'
    ]

class ItemCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """"
    list: API Endpoint for returning a set of item categories.

    retrieve: API endpoint for return a particular item categories.
    """
    queryset = models.ItemCategory.objects.all().order_by('pk')
    serializer_class = serializers.ItemCategorySerializer


class WeaponFilterSet(FilterSet):

    # returns a filter method to a given WeaponProperty
    def weapon_property_filter(property_name):
        return lambda queryset, name, value: (
            queryset.filter(properties__property__name__iexact=property_name)
        )

    is_light = BooleanFilter(label='Is Light', method=weapon_property_filter('light'))
    is_versatile = BooleanFilter(label='Is Versatile', method=weapon_property_filter('versatile'))
    is_thrown = BooleanFilter(label='Is Thrown', method=weapon_property_filter('thrown'))
    is_finesse = BooleanFilter(label='Is Finesse', method = weapon_property_filter('finesse'))
    is_two_handed = BooleanFilter(label='Is Two-handed', method=weapon_property_filter('two-handed'))

    class Meta:
        model = models.Weapon
        fields = {
            'key': ['in', 'iexact'],
            'name': ['iexact'],
            'document__key': ['in','iexact'],
            'document__gamesystem__key': ['in','iexact'],
            'damage_dice': ['in','iexact'],
        }


class WeaponViewSet(EagerLoadingMixin, viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of weapons.
    retrieve: API endpoint for returning a particular weapon.
    """
    queryset = models.Weapon.objects.all().order_by('pk')
    serializer_class = serializers.WeaponSerializer
    filterset_class = WeaponFilterSet

    prefetch_related_fields = ['document', 'damage_type', 'properties__property']

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
