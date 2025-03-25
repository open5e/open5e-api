"""Serializer for the CharacterClass and Feature, and FeatureItem models."""

from rest_framework import serializers

from api_v2 import models

from .abstracts import GameContentSerializer
from .document import DocumentSummarySerializer


class ClassFeatureItemSerializer(GameContentSerializer):
    class Meta:
        model = models.ClassFeatureItem
        fields = ['level', 'detail']

class ClassFeatureColumnItemSerializer(GameContentSerializer):
    class Meta:
        model = models.ClassFeatureItem
        fields = ['level', 'column_value']

class ClassFeaturePrefetchSerializer(GameContentSerializer):
    class Meta:
        model = models.ClassFeatureItem
        fields = ['level', 'detail', 'column_value']

class ClassFeatureSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    feature_items = ClassFeaturePrefetchSerializer(many=True, read_only=True)

    def to_representation(self, instance):
        # run 'to_representation' on super-class (GameContentSerializer)
        representation = super().to_representation(instance)

        # Filters non-table data from FeatureItems
        gained_at = [
            ClassFeatureItemSerializer(item).data
            for item in instance.feature_items.all()
            if item.column_value is None
        ]

        # Filters table data from FeatureItems
        table_data = [
            ClassFeatureColumnItemSerializer(item).data
            for item in instance.feature_items.all()
            if item.column_value is not None
        ]

        # replace 'feature_items' with 'gained_at' and 'column_data' in representation
        representation['gained_at'] = gained_at
        representation['table_data'] = table_data
        del representation['feature_items']

        return representation

    class Meta:
        model = models.ClassFeature
        fields = [
            'key',
            'name',
            'desc',
            'feature_type',
            'feature_items'
        ]

class CharacterClassSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    features = ClassFeatureSerializer(many=True, read_only=True)
    hit_points = serializers.ReadOnlyField()
    document = DocumentSummarySerializer()

    class Meta:
        model = models.CharacterClass
        fields = '__all__'

class CharacterClassSummarySerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    class Meta:
        model = models.CharacterClass
        fields = ['name', 'key']
