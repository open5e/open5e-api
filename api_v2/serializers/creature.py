"""Serializers and helper methods for the Creature model."""

from math import floor

from rest_framework import serializers

from api_v2 import models

from .abstracts import GameContentSerializer
from .size import SizeSerializer


class CreatureActionAttackSerializer(serializers.ModelSerializer):

    distance_unit = serializers.SerializerMethodField()

    class Meta:
        model = models.CreatureActionAttack
        fields = '__all__'

    def get_distance_unit(self, CreatureActionAttack):
        return CreatureActionAttack.get_distance_unit


class CreatureActionSerializer(serializers.ModelSerializer):
    key = serializers.ReadOnlyField()
    attacks = CreatureActionAttackSerializer(many=True, context={'request': {}})

    class Meta:
        model = models.CreatureAction
        fields = '__all__'


class CreatureTypeSerializer(GameContentSerializer):
    '''Serializer for the Creature Type object'''
    key = serializers.ReadOnlyField()

    class Meta:
        '''Meta options for serializer.'''
        model = models.CreatureType
        fields = '__all__'


class CreatureSerializer(GameContentSerializer):
    '''The serializer for the Creature object.'''

    key = serializers.ReadOnlyField()
    ability_scores = serializers.SerializerMethodField()
    modifiers = serializers.SerializerMethodField()
    saving_throws = serializers.SerializerMethodField()
    saving_throws_all = serializers.SerializerMethodField()
    skill_bonuses = serializers.SerializerMethodField()
    skill_bonuses_all = serializers.SerializerMethodField()
    actions = CreatureActionSerializer(many=True, context={'request': {}})
    speed = serializers.SerializerMethodField()
    speed_all = serializers.SerializerMethodField()
    challenge_rating_text = serializers.SerializerMethodField()
    experience_points = serializers.SerializerMethodField()


    class Meta:
        '''Serializer meta options.'''
        model = models.Creature
        fields = [
            'url',
            'document',
            'key',
            'name',
            'size',
            'speed',
            'speed_all',
            'category',
            'subcategory',
            'type',
            'alignment',
            'languages',
            'armor_class',
            'hit_points',
            'hit_dice',
            'challenge_rating_decimal',
            'challenge_rating_text',
            'experience_points',
            'ability_scores',
            'modifiers',
            'saving_throws',
            'saving_throws_all',
            'skill_bonuses',
            'skill_bonuses_all',
            'passive_perception',
            'damage_immunities',
            'nonmagical_attack_immunity',
            'damage_resistances',
            'nonmagical_attack_resistance',
            'damage_vulnerabilities',
            'condition_immunities',
            'normal_sight_range',
            'darkvision_range',
            'blindsight_range',
            'tremorsense_range',
            'truesight_range',
            'actions',
            'creaturesets'
        ]

    def get_ability_scores(self, creature):
        '''Ability scores helper method.'''
        return creature.get_ability_scores()

    def get_modifiers(self, creature):
        '''Modifiers helper method.'''
        return creature.get_modifiers()

    def get_saving_throws(self, creature):
        '''Explicit saving throws helper method.'''
        entries = creature.get_saving_throws().items()
        return { key: value for key, value in entries if value is not None }

    def get_saving_throws_all(self, creature):
        '''Implicit saving throws helper method.'''
        defaults = creature.get_modifiers()
        entries = creature.get_saving_throws().items()
        return { key: (defaults[key] if value is None else value) for key, value in entries }

    def get_skill_bonuses(self, creature):
        '''Explicit skill bonuses helper method.'''
        entries = creature.get_skill_bonuses().items()
        return { key: value for key, value in entries if value is not None }

    def get_skill_bonuses_all(self, creature):
        '''Implicit skill bonuses helper method.'''
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

    def get_speed(self, creature):
        '''Explicit speed helper method.'''
        entries = creature.get_speed().items()
        return { key: value for key, value in entries if value is not None }

    def get_speed_all(self, creature):
        '''Implicit speed helper method.'''
        return creature.get_speed_all()

    def get_challenge_rating_text(self, creature):
        return creature.challenge_rating_text

    def get_experience_points(self, creature):
        return creature.experience_points


class CreatureSetSerializer(GameContentSerializer):
    '''Serializer for the Creature Set object'''
    key = serializers.ReadOnlyField()
    creatures = CreatureSerializer(many=True, read_only=True, context={'request':{}})

    class Meta:
        '''Meta options for serializer.'''
        model = models.CreatureSet
        fields = '__all__'
