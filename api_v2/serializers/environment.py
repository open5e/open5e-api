"""Serializer for the Environment model."""

from rest_framework import serializers

from api_v2 import models

from .abstracts import GameContentSerializer

class EnvironmentSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()

    class Meta:
        model = models.Environment
        fields = '__all__'
