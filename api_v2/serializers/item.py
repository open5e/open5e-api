"""Serializer for the Item, Itemset, armor, and weapon models"""

from rest_framework import serializers

from api_v2 import models

from .abstracts import GameContentSerializer
from .size import SizeSerializer



class ArmorSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    ac_display = serializers.ReadOnlyField()

    class Meta:
        model = models.Armor
        fields = '__all__'

class WeaponSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    is_versatile = serializers.ReadOnlyField()
    is_martial = serializers.ReadOnlyField()
    is_melee = serializers.ReadOnlyField()
    ranged_attack_possible = serializers.ReadOnlyField()
    range_melee = serializers.ReadOnlyField()
    is_reach = serializers.ReadOnlyField()
    properties = serializers.ReadOnlyField()

    class Meta:
        model = models.Weapon
        fields = '__all__'

class ItemRaritySerializer(GameContentSerializer):
    key=serializers.ReadOnlyField()

    class Meta:
        model = models.ItemRarity
        fields = '__all__'

class ItemSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    is_magic_item = serializers.ReadOnlyField()

    class Meta:
        model = models.Item
        fields = '__all__'


class ItemSetSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    items = ItemSerializer(many=True, read_only=True, context={'request':{}})

    class Meta:
        model = models.ItemSet
        fields = '__all__'


class ItemCategorySerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    item_set = ItemSerializer(many=True, read_only=True, context={'request':{}})

    class Meta:
        model = models.ItemCategory
        fields = "__all__"