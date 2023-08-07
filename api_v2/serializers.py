from rest_framework import serializers

from api_v2 import models


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

            depth = self.context['request'].query_params.get('depth')
            if depth:
                try:
                    depth_value = int(depth)
                    if depth_value > 0 and depth_value < 3:
                        # This value going above 1 could cause performance issues.
                        # Limited to 1 and 2 for now.
                        self.Meta.depth = depth_value
                        # Depth does not reset by default on subsequent requests with malformed urls.
                    else:
                        self.Meta.depth = 0
                except ValueError:
                    pass  # it was not castable to an int.
            else:
                self.Meta.depth = 0 #The default.

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
    weapon = WeaponSerializer(read_only=True, context={'request': {}})
    armor = ArmorSerializer(read_only=True, context={'request': {}})


    class Meta:
        model = models.Item
        fields = '__all__'


class ItemSetSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    items = ItemSerializer(many=True, read_only=True, context={'request':{}})

    class Meta:
        model = models.ItemSet
        fields = '__all__'


class CreatureSerializer(GameContentSerializer):

    key = serializers.ReadOnlyField()
    ability_scores = serializers.SerializerMethodField()
    modifiers = serializers.SerializerMethodField()
    saving_throws = serializers.SerializerMethodField()
    all_saving_throws = serializers.SerializerMethodField()
    skill_bonuses = serializers.SerializerMethodField()
    all_skill_bonuses = serializers.SerializerMethodField()

    class Meta:
        model = models.Creature
        fields = [
            'url',
            'document',
            'key',
            'name',
            'desc',
            'size',
            'armor_class',
            'ability_scores',
            'modifiers',
            'saving_throws',
            'all_saving_throws',
            'skill_bonuses',
            'all_skill_bonuses',
            'passive_perception',
        ]

    def get_ability_scores(self, monster):
        return monster.get_ability_scores()

    def get_modifiers(self, monster):
        return monster.get_modifiers()

    def get_saving_throws(self, monster):
        entries = monster.get_saving_throws().items()
        return { key: value for key, value in entries if value is not None }

    def get_all_saving_throws(self, monster):
        defaults = monster.get_modifiers()
        entries = monster.get_saving_throws().items()
        return { key: (defaults[key] if value is None else value) for key, value in entries }

    def get_skill_bonuses(self, monster):
        entries = monster.get_skill_bonuses().items()
        return { key: value for key, value in entries if value is not None }

    def get_all_skill_bonuses(self, monster):
        defaults = {
            'acrobatics': monster.modifier_dexterity,
            'animal_handling': monster.modifier_wisdom,
            'arcana': monster.modifier_intelligence,
            'athletics': monster.modifier_strength,
            'deception': monster.modifier_charisma,
            'history': monster.modifier_intelligence,
            'insight': monster.modifier_wisdom,
            'intimidation': monster.modifier_charisma,
            'investigation': monster.modifier_intelligence,
            'medicine': monster.modifier_wisdom,
            'nature': monster.modifier_intelligence,
            'perception': monster.modifier_wisdom,
            'performance': monster.modifier_charisma,
            'persuasion': monster.modifier_charisma,
            'religion': monster.modifier_intelligence,
            'sleight_of_hand': monster.modifier_dexterity,
            'stealth': monster.modifier_dexterity,
            'survival': monster.modifier_wisdom,
        }
        entries = monster.get_skill_bonuses().items()
        return { key: (defaults[key] if value is None else value) for key, value in entries }
