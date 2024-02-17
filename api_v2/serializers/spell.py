"""Serializers for the Trait and Race models."""

from rest_framework import serializers

from api_v2 import models

from .abstracts import GameContentSerializer

class SpellSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    slot_expended=serializers.ReadOnlyField()
    casting_options=serializers.ReadOnlyField()

    class Meta:
        model = models.Spell
        fields = '__all__'

