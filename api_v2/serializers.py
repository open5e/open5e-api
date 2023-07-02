from rest_framework import serializers

from api_v2 import models

from rest_framework import serializers

class GameContentSerializer(serializers.HyperlinkedModelSerializer):
    # Add all properties as read only to fields
    # Adding dynamic "fields" qs parameter.
    def __init__(self, *args, **kwargs):
        # Instantiate the superclass normally
        super(GameContentSerializer, self).__init__(*args, **kwargs)

        # The request doesn't exist when generating an OAS file, so we have to check that first
        if self.context['request']:
            fields = self.context['request'].query_params.get('fields')
            if fields:
                fields = fields.split(',')
                # Drop any fields that are not specified in the `fields` argument.
                allowed = set(fields)
                existing = set(self.fields.keys())
                for field_name in existing - allowed:
                    self.fields.pop(field_name)

    class Meta:
        abstract = True


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
            'url',
            'name',
            'ac_display',
            'strength_score_required',
            'grants_stealth_disadvantage'
        ]


class ArmorSerializerFull(GameContentSerializer):
    ac_display = serializers.ReadOnlyField()

    class Meta:
        model = models.Armor
        fields = "__all__"


class WeaponSerializerSimple(serializers.ModelSerializer):

    class Meta:
        model = models.Weapon
        fields = [
            'url',
            'name',
            'properties']


class WeaponSerializerFull(GameContentSerializer):
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


class ItemSetSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.ItemSet
        fields = "__all__"


class ItemSerializerFull(GameContentSerializer):
    weapon = WeaponSerializerSimple()
    armor = ArmorSerializerSimple()

    is_magic_item = serializers.ReadOnlyField()

    class Meta:
        model = models.Item
        fields = ['url','cost','weapon','armor','document','category',
            'requires_attunement','rarity','is_magic_item',
            'itemsets']