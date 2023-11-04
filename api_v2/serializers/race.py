"""Serializers for the Trait and Race models."""

from rest_framework import serializers

from api_v2 import models

from .abstracts import GameContentSerializer


class TraitSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Trait
        fields = ['name', 'desc']


class RaceSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    is_subrace = serializers.ReadOnlyField()
    is_selectable = serializers.ReadOnlyField()
    traits = TraitSerializer(
        many=True)

    class Meta:
        model = models.Race
        fields = '__all__'

