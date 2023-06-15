from rest_framework import serializers

from api_v2 import models


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Document
        fields = [
            'slug',
            'abbr',
            'name',
            'license',
            'organization',
            'author',
            'published_at',
            'permalink'
        ]


class ArmorTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.ArmorType
        fields = [
            'slug',
            'name',
            'ac_display',
            'strength_score_required',
            'grants_stealth_disadvantage'
        ]


class WeaponTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.WeaponType
        fields = [
            'slug',
            'name',
            'properties']


class MagicItemTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.MagicItemType
        fields = [
            'slug',
            'name',
            'rarity',
            'requires_attunement']


class ItemSerializer(serializers.ModelSerializer):
    weapon_type = WeaponTypeSerializer()
    armor_type = ArmorTypeSerializer()
    magic_item_type = MagicItemTypeSerializer()
    
    class Meta:
        model = models.Item
        fields = [
            'slug',
            'name',
            'weight',
            'is_weapon',
            'weapon_type',
            'is_armor',
            'armor_type',
            'is_magic_item',
            'magic_item_type',
            'cost'
            ]

