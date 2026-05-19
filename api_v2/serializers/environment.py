"""Serializer for the Environment model."""

from rest_framework import serializers

from api_v2 import models

from .abstracts import GameContentSerializer

class EnvironmentSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()

    class Meta:
        model = models.Environment
        fields = '__all__'

class EnvironmentSummarySerializer(GameContentSerializer):
    '''
    A slimmer EnvironmentSerializer, designed to serialize Enviroment FKs on
    other serializers. ie. The `environments` field on the CreatureSerializer.
    Not intended to be used directly in a ModelViewset.
    '''
    class Meta:
        model = models.Environment
        fields = ['name', 'key']