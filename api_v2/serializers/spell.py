"""Serializers for the Trait and Race models."""

from rest_framework import serializers

from api_v2 import models

from .abstracts import GameContentSerializer

class SpellSchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SpellSchool
        fields='__all__'


class CastingOptionSerializer(serializers.ModelSerializer):
#    type=serializers.ReadOnlyField()
#    damage_roll = serializers.ReadOnlyField()
#    duration = serializers.ReadOnlyField()
#    range = serializers.ReadOnlyField()
#    target_count = serializers.ReadOnlyField()

    class Meta:
        model = models.CastingOption
        exclude = ['id','spell']
       # fields = '__all__'


class SpellSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    slot_expended=serializers.ReadOnlyField()
    casting_options = CastingOptionSerializer(many=True)
    school = SpellSchoolSerializer()

    class Meta:
        model = models.Spell
        fields = '__all__'
