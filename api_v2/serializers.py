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


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Document
        fields = [
            'key',
            'url',
            'name',
            'desc',
            'publisher',
            'ruleset',
            'license',
            'author',
            'published_at',
            'permalink'
        ]


class ArmorSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Armor
        fields = [
            'key',
            'name',
            'ac_display',
            'strength_score_required',
            'grants_stealth_disadvantage'
        ]


class WeaponSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Weapon
        fields = [
            'key',
            'url',
            'name',
            'properties']


class MagicItemTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.MagicItemType
        fields = [
            'key',
            'name',
            'rarity',
            'requires_attunement']


class ItemSerializer(serializers.ModelSerializer):
    weapon = WeaponSerializer()
    armor = ArmorSerializer()
    magic_item_type = MagicItemTypeSerializer()

    document = serializers.HyperlinkedRelatedField(
        view_name='document-detail',
        read_only=True)

    class Meta:
        model = models.Item
        fields = [
            'key',
            'url',
            'name',
            'desc',
            'document',
            'weight',
            'is_weapon',
            'weapon',
            'is_armor',
            'armor',
            'is_magic_item',
            'magic_item_type',
            'cost']
