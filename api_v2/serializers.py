from rest_framework import serializers

from api_v2 import models

# Default set of fields that almost all gamecontent items will have.
GAMECONTENT_FIELDS = ['url', 'key', 'name', 'desc', 'document']


class GameContentSerializer(serializers.HyperlinkedModelSerializer):

    # Adding dynamic "fields" qs parameter.
    def __init__(self, *args, **kwargs):
        # Add default fields variable.

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


class RulesetSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Ruleset
        fields = '__all__'


class LicenseSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.License
        fields = '__all__'


class PublisherSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Publisher
        fields = '__all__'


class DocumentSerializerSimple(serializers.ModelSerializer):
    class Meta:
        model = models.Document
        fields = [
            'key',
            'url']


class DocumentSerializerFull(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Document
        fields = "__all__"


class ArmorSerializerSimple(serializers.ModelSerializer):

    class Meta:
        model = models.Armor
        fields = ['url','key','name','document'] + [
            'ac_display']


class ArmorSerializerFull(GameContentSerializer):
    ac_display = serializers.ReadOnlyField()

    class Meta:
        model = models.Armor
        fields = ['url','key','name','document'] + [
            'ac_display',
            'grants_stealth_disadvantage',
            'strength_score_required',
            'ac_base',
            'ac_add_dexmod',
            'ac_cap_dexmod']


class WeaponSerializerSimple(serializers.ModelSerializer):

    class Meta:
        model = models.Weapon
        fields = ['url','key','name','document'] + [
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
        fields = ['url','key','name','document'] + [ # Remove the DESC field.
            'properties',
            'is_versatile',
            'is_martial',
            'is_melee',
            'range_melee',
            'ranged_attack_possible',
            'is_reach',
            'damage_type',
            'damage_dice',
            'versatile_dice',
            'range_reach',
            'range_normal',
            'range_long',
            'is_finesse',
            'is_thrown',
            'is_two_handed',
            'requires_ammunition',
            'requires_loading',
            'is_heavy',
            'is_light',
            'is_lance',
            'is_net',
            'is_simple',
            'is_improvised']


class ItemSerializerFull(GameContentSerializer):
    weapon = WeaponSerializerSimple()
    armor = ArmorSerializerSimple()

    is_magic_item = serializers.ReadOnlyField()

    class Meta:
        model = models.Item
        fields = GAMECONTENT_FIELDS + [
            'category',
            'cost',
            'weight',
            'weapon',
            'armor',
            'requires_attunement',
            'rarity',
            'is_magic_item']


class ItemSetSerializer(GameContentSerializer):

    class Meta:
        model = models.ItemSet
        fields = GAMECONTENT_FIELDS + [
            'items']