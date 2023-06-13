from rest_framework import serializers

from api_v2 import models


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


class ItemSerializer(serializers.ModelSerializer):
    weapon_type = WeaponTypeSerializer()
    armor_type = ArmorTypeSerializer() 
    
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
            'is_magical',
            'cost'
            ]

