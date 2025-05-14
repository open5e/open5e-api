"""Serializer for the Item, Itemset, armor, and weapon models"""

from rest_framework import serializers

from api_v2 import models

from .abstracts import GameContentSerializer
from .damagetype import DamageTypeSummarySerializer
from .document import DocumentSummarySerializer
from .size import SizeSummarySerializer
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes


class ArmorSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    ac_display = serializers.ReadOnlyField()
    category = serializers.ReadOnlyField()
    document = DocumentSummarySerializer()

    class Meta:
        model = models.Armor
        fields = '__all__'

class ArmorSummarySerializer(GameContentSerializer):
    '''
    A slightly slimmer ArmorSerializer, designed to serialize Armor FKs on
    other serializers. ie. The `armor` field on the ItemSerializer. Not 
    intended to be used directly in a ModelViewset.
    '''
    class Meta:
        model = models.Armor
        fields = [
            'name',
            'key',
            'url',
            'category',
            'ac_base',
            'ac_display',
            'ac_add_dexmod',
            'ac_cap_dexmod',
            'grants_stealth_disadvantage',
            'strength_score_required',
        ]

class WeaponPropertySerializer(GameContentSerializer):
    class Meta:
        model = models.WeaponProperty
        document = DocumentSummarySerializer()
        fields = ['key', 'name', 'desc', 'document']

class WeaponSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    document = DocumentSummarySerializer()
    damage_type = DamageTypeSummarySerializer()
    is_versatile = serializers.ReadOnlyField()
    is_martial = serializers.ReadOnlyField()
    is_melee = serializers.ReadOnlyField()
    ranged_attack_possible = serializers.ReadOnlyField()
    range_melee = serializers.ReadOnlyField()
    is_reach = serializers.ReadOnlyField()
    properties = serializers.ReadOnlyField()
    distance_unit = serializers.SerializerMethodField()

    class Meta:
        model = models.Weapon
        fields = '__all__'

    # todo: type is any
    @extend_schema_field(OpenApiTypes.STR)
    def get_distance_unit(self, Weapon):
        return Weapon.get_distance_unit

class WeaponSummarySerializer(GameContentSerializer):
    '''
    A (slightly) more slender version of the WeaponSerializer. Designed for 
    serializing FKs to the Weapons table in other serializers – ie. the 
    `"weapon"` field on the ItemSerializer
    '''
    damage_type = DamageTypeSummarySerializer()
    is_versatile = serializers.ReadOnlyField()
    is_martial = serializers.ReadOnlyField()
    is_melee = serializers.ReadOnlyField()
    is_finesse = serializers.ReadOnlyField()
    ranged_attack_possible = serializers.ReadOnlyField()
    range_melee = serializers.ReadOnlyField()
    is_reach = serializers.ReadOnlyField()
    properties = serializers.ReadOnlyField()
    distance_unit = serializers.SerializerMethodField()

    class Meta:
        model = models.Weapon
        fields = [
            'name',
            'key',
            'url',
            'damage_type',
            'damage_dice',
            'versatile_dice',
            'is_versatile',
            'reach',
            'is_reach',
            'is_finesse',
            'range',
            'range_melee',
            'long_range',
            'ranged_attack_possible',
            'is_thrown',
            'is_two_handed',
            'requires_ammunition',
            'requires_loading',
            'is_heavy',
            'is_light',
            'is_lance',
            'is_net',
            'is_melee',
            'is_simple',
            'is_martial',
            'is_improvised',
            'properties',
            'distance_unit',
        ]
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_distance_unit(self, Weapon):
        return Weapon.get_distance_unit

class ItemRaritySerializer(GameContentSerializer):
    class Meta:
        model = models.ItemRarity
        fields = ['name', 'url', 'key', 'rank']

class ItemCategorySerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    document = DocumentSummarySerializer()
    class Meta:
        model = models.ItemCategory
        fields = '__all__'

class ItemCategorySummarySerializer(GameContentSerializer):
    class Meta:
        model = models.ItemCategory
        fields = ['name', 'key', 'url']

class ItemSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    is_magic_item = serializers.ReadOnlyField()
    weapon = WeaponSummarySerializer()
    armor = ArmorSummarySerializer()
    document = DocumentSummarySerializer()
    category = ItemCategorySummarySerializer()
    rarity = ItemRaritySerializer()
    damage_immunities = DamageTypeSummarySerializer(many=True)
    size = SizeSummarySerializer()
    weight_unit = serializers.SerializerMethodField()
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_weight_unit(self, item):
        return item.get_weight_unit()

    class Meta:
        model = models.Item
        fields = '__all__'

class ItemSummarySerializer(GameContentSerializer):
    class Meta:
        model = models.Item
        fields = ['name', 'key', 'url']



class ItemSetSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    items = ItemSummarySerializer(many=True, read_only=True)

    class Meta:
        model = models.ItemSet
        fields = '__all__'
