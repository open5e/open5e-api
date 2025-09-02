"""Serializer for the DamageType model."""

from rest_framework import serializers

from api_v2 import models

from .abstracts import GameContentSerializer
from .abstracts import DescriptionSerializer


class SkillDescriptionSerializer(DescriptionSerializer):
    class Meta:
        model=models.SkillDescription
        fields=['desc','document']


class SkillSerializer(serializers.ModelSerializer):
    descriptions = SkillDescriptionSerializer(many=True)

    class Meta:
        model = models.Skill
        fields = '__all__'


class AbilityDescriptionSerializer(DescriptionSerializer):
    class Meta:
        model=models.AbilityDescription
        fields=['desc','document']


class AbilitySerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    descriptions = AbilityDescriptionSerializer(many=True)

    skills = SkillSerializer(
        many=True
    )

    class Meta:
        model = models.Ability
        fields = '__all__'



class AbilitySummarySerializer(GameContentSerializer):
    '''
    A slimmer AbilitySerializer, designed to serialize Ability FKs on other 
    serializers. ie. The `saving_throws` field on CharacterClassSerializer. Not
    intended to be used directly with in a ModelViewset.
    '''
    class Meta:
        model = models.Ability
        fields = ['name', 'url']