"""Serializer for the CharacterClass and Feature, and FeatureItem models."""

from rest_framework import serializers

from api_v2 import models

from .abstracts import GameContentSerializer

class ClassFeatureItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ClassFeatureItem
        fields = ['name','desc','type']

class ClassFeatureSerializer(serializers.ModelSerializer):
    key = serializers.ReadOnlyField()

    class Meta:
        model = models.ClassFeature
        fields = ['key', 'name', 'desc']

class CharacterClassSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    features = ClassFeatureSerializer(
        many=True, context={'request': {}})
    levels = serializers.ReadOnlyField()
    hit_points = serializers.ReadOnlyField()

    class Meta:
        model = models.CharacterClass
        fields = '__all__'
