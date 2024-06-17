"""Serializers for the Trait and Race models."""

from rest_framework import serializers

from api_v2 import models

from .abstracts import GameContentSerializer

class SpellSchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SpellSchool
        fields='__all__'


class SpellCastingOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SpellCastingOption
        exclude = ['id','parent']


class SpellSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    slot_expended=serializers.ReadOnlyField()
    casting_options = SpellCastingOptionSerializer(many=True)
    school = SpellSchoolSerializer()

    class Meta:
        model = models.Spell
        fields = '__all__'
