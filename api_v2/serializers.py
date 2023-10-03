from math import floor
from rest_framework import serializers
from django.core.exceptions import ObjectDoesNotExist

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

class FeatBenefitSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.FeatBenefit
        fields = ['desc']

class FeatSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    has_prerequisite = serializers.ReadOnlyField()
    benefits = FeatBenefitSerializer(
        many=True)

    class Meta:
        model = models.Feat
        fields = '__all__'


class TraitSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Trait
        fields = ['name', 'desc']


class RaceSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    is_subrace = serializers.ReadOnlyField()
    is_selectable = serializers.ReadOnlyField()
    traits = TraitSerializer(
        many=True)

    class Meta:
        model = models.Race
        fields = '__all__'

def calc_damage_amount(die_count, die_type, bonus):
    die_values = {
        'D4': 2.5,
        'D6': 3.5,
        'D8': 4.5,
        'D10': 5.5,
        'D12': 6.5,
        'D20': 10.5,
    }
    return floor(die_count * die_values[die_type] + bonus)

def make_damage_obj(die_count, die_type, bonus, damage_type):
    if die_count:
        return {
            'amount': calc_damage_amount(
                die_count,
                die_type,
                bonus
            ),
            'die_count': die_count,
            'die_type': die_type,
            'bonus': bonus,
            'type': damage_type,
        }
    return {
        'amount': 1,
        'type': damage_type,
    }

def make_attack_obj(attack):

    obj = {
        'name': attack.name,
        'attack_type': attack.attack_type,
        'to_hit_mod': attack.to_hit_mod,
    }

    if attack.reach_ft:
        obj['reach_ft'] = attack.reach_ft
    if attack.range_ft:
        obj['range_ft'] = attack.range_ft
    if attack.long_range_ft:
        obj['long_range_ft'] = attack.long_range_ft

    obj['target_creature_only'] = attack.target_creature_only

    if attack.damage_type:
        obj['damage'] = make_damage_obj(
            attack.damage_die_count,
            attack.damage_die_type,
            attack.damage_bonus,
            attack.damage_type
        )

    if attack.extra_damage_type:
        obj['extra_damage'] = make_damage_obj(
            attack.extra_damage_die_count,
            attack.extra_damage_die_type,
            attack.extra_damage_bonus,
            attack.extra_damage_type
        )

    return obj

def make_action_obj(action):

    obj = { 'name': action.name, 'desc': action.desc }

    match action.uses_type:
        case 'PER_DAY':
            obj['uses_per_day'] = action.uses_param
        case 'RECHARGE_ON_ROLL':
            obj['recharge_on_roll'] = action.uses_param
        case 'RECHARGE_AFTER_REST':
            obj['recharge_after_rest'] = True

    attacks = action.creatureattack_set.all()

    if len(attacks) > 0:
        obj['attacks'] = [make_attack_obj(attack) for attack in attacks]

    return obj

class CreatureSerializer(GameContentSerializer):

    key = serializers.ReadOnlyField()
    ability_scores = serializers.SerializerMethodField()
    modifiers = serializers.SerializerMethodField()
    saving_throws = serializers.SerializerMethodField()
    all_saving_throws = serializers.SerializerMethodField()
    skill_bonuses = serializers.SerializerMethodField()
    all_skill_bonuses = serializers.SerializerMethodField()
    actions = serializers.SerializerMethodField()

    class Meta:
        model = models.Creature
        fields = [
            'url',
            'document',
            'key',
            'name',
            'category',
            'size',
            'type',
            'subtype',
            'alignment',
            'weight',
            'armor_class',
            'hit_points',
            'ability_scores',
            'modifiers',
            'saving_throws',
            'all_saving_throws',
            'skill_bonuses',
            'all_skill_bonuses',
            'passive_perception',
            'actions',
        ]

    def get_ability_scores(self, creature):
        return creature.get_ability_scores()

    def get_modifiers(self, creature):
        return creature.get_modifiers()

    def get_saving_throws(self, creature):
        entries = creature.get_saving_throws().items()
        return { key: value for key, value in entries if value is not None }

    def get_all_saving_throws(self, creature):
        defaults = creature.get_modifiers()
        entries = creature.get_saving_throws().items()
        return { key: (defaults[key] if value is None else value) for key, value in entries }

    def get_skill_bonuses(self, creature):
        entries = creature.get_skill_bonuses().items()
        return { key: value for key, value in entries if value is not None }

    def get_all_skill_bonuses(self, creature):
        defaults = {
            'acrobatics': creature.modifier_dexterity,
            'animal_handling': creature.modifier_wisdom,
            'arcana': creature.modifier_intelligence,
            'athletics': creature.modifier_strength,
            'deception': creature.modifier_charisma,
            'history': creature.modifier_intelligence,
            'insight': creature.modifier_wisdom,
            'intimidation': creature.modifier_charisma,
            'investigation': creature.modifier_intelligence,
            'medicine': creature.modifier_wisdom,
            'nature': creature.modifier_intelligence,
            'perception': creature.modifier_wisdom,
            'performance': creature.modifier_charisma,
            'persuasion': creature.modifier_charisma,
            'religion': creature.modifier_intelligence,
            'sleight_of_hand': creature.modifier_dexterity,
            'stealth': creature.modifier_dexterity,
            'survival': creature.modifier_wisdom,
        }
        entries = creature.get_skill_bonuses().items()
        return { key: (defaults[key] if value is None else value) for key, value in entries }

    def get_actions(self, creature):
        result = []
        for action in creature.creatureaction_set.all():
            # item = { 'name': action.name, 'desc': action.desc }
            # match action.uses_type:
            #     case 'PER_DAY':
            #         item['uses_per_day'] = action.uses_param
            #     case 'RECHARGE_ON_ROLL':
            #         item['recharge_on_roll'] = action.uses_param
            #     case 'RECHARGE_AFTER_REST':
            #         item['recharge_after_rest'] = True
            # try:
            #     attack = models.CreatureAttackAction.objects.get(pk=action.key)
            #     item['attack_type'] = attack.attack_type
            #     item['to_hit_mod'] = attack.to_hit_mod
            #     if attack.reach_ft:
            #         item['reach_ft'] = attack.reach_ft
            #     if attack.range_ft:
            #         item['range_ft'] = attack.range_ft
            #     if attack.long_range_ft:
            #         item['long_range_ft'] = attack.long_range_ft
            #     item['target_creature_only'] = attack.target_creature_only
            #     if attack.damage_type:
            #         item['damage'] = make_damage_obj(
            #             attack.damage_die_count,
            #             attack.damage_die_type,
            #             attack.damage_bonus,
            #             attack.damage_type
            #         )
            #     if attack.extra_damage_type:
            #         item['extra_damage'] = make_damage_obj(
            #             attack.extra_damage_die_count,
            #             attack.extra_damage_die_type,
            #             attack.extra_damage_bonus,
            #             attack.extra_damage_type
            #         )
            #     if attack.versatile_weapon:
            #         item['two_handed_damage'] = make_damage_obj(
            #             attack.damage_die_count,
            #             attack.versatile_weapon,
            #             attack.damage_bonus,
            #             attack.damage_type
            #         )
            # except ObjectDoesNotExist:
            #     pass
            # result.append(item)
            action_obj = make_action_obj(action)
            result.append(action_obj)
        return result


class BackgroundBenefitSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BackgroundBenefit
        fields = ['name','desc']

class BackgroundSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    backgroundbenefit_set = BackgroundBenefitSerializer(
        many=True
    )

    class Meta:
        model = models.Background
        fields = '__all__'
