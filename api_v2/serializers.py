from rest_framework import serializers

from api_v2 import models


class LicenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.License
        fields = '__all__'


class PublisherSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Publisher
        fields = '__all__'

class DocumentSerializerSimple(serializers.ModelSerializer):
    class Meta:
        model = models.Document
        fields = [
            'key',
            'url']


class DocumentSerializerFull(serializers.ModelSerializer):
    class Meta:
        model = models.Document
        fields = "__all__"


class ArmorSerializerSimple(serializers.ModelSerializer):

    class Meta:
        model = models.Armor
        fields = [
            'key',
            'url',
            'name',
            'ac_display',
            'strength_score_required',
            'grants_stealth_disadvantage'
        ]


class ArmorSerializerFull(serializers.ModelSerializer):
    ac_display = serializers.ReadOnlyField()

    class Meta:
        model = models.Armor
        fields = "__all__"


class WeaponSerializerSimple(serializers.ModelSerializer):

    class Meta:
        model = models.Weapon
        fields = [
            'key',
            'url',
            'name',
            'properties']


class WeaponSerializerFull(serializers.ModelSerializer):
    is_versatile = serializers.ReadOnlyField()
    is_martial = serializers.ReadOnlyField()
    is_melee = serializers.ReadOnlyField()
    ranged_attack_possible = serializers.ReadOnlyField()
    range_melee = serializers.ReadOnlyField()
    is_reach = serializers.ReadOnlyField()
    properties = serializers.ReadOnlyField()

    class Meta:
        model = models.Weapon
        fields = "__all__"


class ItemSerializer(serializers.ModelSerializer):
    weapon = WeaponSerializerSimple()
    armor = ArmorSerializerSimple()
    document = DocumentSerializerSimple()

    class Meta:
        model = models.Item
        fields = [
            'key',
            'url',
            'name',
            'desc',
            'document',
            'weight',
            'weapon',
            'armor',
            'is_magic_item',
            'requires_attunement',
            'rarity',
            'cost',
            'itemset_set']


class ItemSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ItemSet
        fields = "__all__"