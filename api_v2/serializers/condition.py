"""Serializer for the Condition model."""

from rest_framework import serializers

from api_v2 import models

from .abstracts import GameContentSerializer

class ConditionSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()

    class Meta:
        model = models.Condition
        fields = '__all__'
