"""Serializer for the DamageType model."""

from rest_framework import serializers

from api_v2 import models

from .abstracts import GameContentSerializer

class DamageTypeSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()

    class Meta:
        model = models.DamageType
        fields = '__all__'
