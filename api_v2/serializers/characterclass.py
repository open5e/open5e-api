"""Serializer for the CharacterClass and Feature, and FeatureItem models."""

from rest_framework import serializers

from api_v2 import models

from .abstracts import GameContentSerializer

class FeatureItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.FeatureItem
        fields = ['name','desc','type']

class FeatureSerializer(serializers.ModelSerializer):
    key = serializers.ReadOnlyField()

    class Meta:
        model = models.Feature
        fields = ['key', 'name', 'desc']

class CharacterClassSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    features = FeatureSerializer(
        many=True, context={'request': {}})
    levels = serializers.ReadOnlyField()

    class Meta:
        model = models.CharacterClass
        fields = '__all__'
