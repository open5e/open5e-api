"""Serializer for the CharacterClass and Feature, and FeatureItem models."""

from rest_framework import serializers

from api_v2 import models

from .abstracts import GameContentSerializer
from .document import DocumentSerializer


class ClassFeatureItemSerializer(GameContentSerializer):
    
    class Meta:
        model = models.ClassFeatureItem
        fields = ['level']

class ClassFeatureColumnItemSerializer(GameContentSerializer):
    class Meta:
        model = models.ClassFeatureItem
        fields = ['level','column_value']

class ClassFeatureSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    featureitems = ClassFeatureItemSerializer(
        many=True
    )

    columnitems = ClassFeatureColumnItemSerializer(
        many=True
    )

    class Meta:
        model = models.ClassFeature
        fields = ['key', 'name', 'desc','featureitems','columnitems', 'feature_type']

class CharacterClassSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    features = ClassFeatureSerializer(
        many=True, context={'request': {}})
    hit_points = serializers.ReadOnlyField()
    document = DocumentSerializer()

    class Meta:
        model = models.CharacterClass
        fields = '__all__'
