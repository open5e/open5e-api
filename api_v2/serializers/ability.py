"""Serializer for the DamageType model."""

from rest_framework import serializers

from api_v2 import models

from .abstracts import GameContentSerializer

class SkillSerializer(serializers.ModelSerializer):
    desc = serializers.SerializerMethodField()

    class Meta:
        model = models.Skill
        fields = ['key','name','desc']

    def get_desc(self, Skill):
        return Skill.get_desc.desc


class AbilitySerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    desc = serializers.SerializerMethodField()

    skills = SkillSerializer(
        many=True
    )

    class Meta:
        model = models.Ability
        fields = '__all__'

    def get_desc(self, Ability):
        return Ability.get_desc.desc


class AbilitySummarySerializer(GameContentSerializer):
    '''
    A slimmer AbilitySerializer, designed to serialize Ability FKs on other 
    serializers. ie. The `saving_throws` field on CharacterClassSerializer. Not
    intended to be used directly with in a ModelViewset.
    '''
    class Meta:
        model = models.Ability
        fields = ['name', 'url']