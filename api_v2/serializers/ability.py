"""Serializer for the DamageType model."""

from rest_framework import serializers

from api_v2 import models

from .abstracts import GameContentSerializer

class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Skill
        fields = ['key','name','desc']


class AbilitySerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    skills = SkillSerializer(
        many=True
    )

    class Meta:
        model = models.Ability
        fields = '__all__'
