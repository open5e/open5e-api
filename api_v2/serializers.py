from rest_framework import serializers

from api_v2 import models


class GameContentSerializer(serializers.HyperlinkedModelSerializer):
    
    # Adding dynamic "fields" qs parameter.
    def __init__(self, *args, **kwargs):
        # Add default fields variable.

        # Instantiate the superclass normally
        super(GameContentSerializer, self).__init__(*args, **kwargs)

        # Add all read-only fields.
       # setattr(self.Meta, 'read_only_fields', [*self.fields])

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

            depth = self.context['request'].query_params.get('depth')
            if depth:
                try:
                    depth_value = int(depth)
                    if depth_value > 0 and depth_value < 3:
                        self.Meta.depth = depth_value
                        #This value going above 1 could massively cause performance issues.
                    else: 
                        self.Meta.depth = 0
                except ValueError:
                    pass  # it was a string, not an int.
            else:
                # Depth does not reset by default on subsequent requests with malformed urls.
                self.Meta.depth = 0

    class Meta:
        abstract = True


class RulesetSerializer(serializers.HyperlinkedModelSerializer):
    key = serializers.ReadOnlyField()

    class Meta:
        model = models.Ruleset
        fields = '__all__'


class LicenseSerializer(serializers.HyperlinkedModelSerializer):
    key = serializers.ReadOnlyField()

    class Meta:
        model = models.License
        fields = '__all__'


class PublisherSerializer(serializers.HyperlinkedModelSerializer):
    key = serializers.ReadOnlyField()

    class Meta:
        model = models.Publisher
        fields = '__all__'


class DocumentSerializer(serializers.HyperlinkedModelSerializer):
    key = serializers.ReadOnlyField()

    class Meta:
        model = models.Document
        fields = "__all__"


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


class ItemSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    is_magic_item = serializers.ReadOnlyField()

    class Meta:
        model = models.Item
        fields = '__all__'


class ItemSetSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()

    class Meta:
        model = models.ItemSet
        fields = '__all__'
