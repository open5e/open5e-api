from rest_framework import serializers

from api_v2 import models


class ArmorTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model =  models.ArmorType
        fields = [
            'slug',
            'name',
            'is_light',
            'is_medium',
            'is_heavy',
            'ac_display',
            'strength_score_required',
        ]

class WeaponTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.WeaponType
        fields = [
            'slug',
            'name',
            'is_simple',
            'is_martial',
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

