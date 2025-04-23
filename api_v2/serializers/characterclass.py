"""Serializer for the CharacterClass and Feature, and FeatureItem models."""

from rest_framework import serializers

from api_v2 import models

from .abstracts import GameContentSerializer
from .document import DocumentSummarySerializer
from .ability import AbilitySummarySerializer

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
        """
        'feature_items' field contains tabulated and non-tabulated data. These
        have different uses and must be split into the 'gained_at' and 
        'table_data' fields before being returned by the serializer
        """
        # run 'to_representation' on super-class (GameContentSerializer)
        representation = super().to_representation(instance)
        
        # Split FeatureItems into tabulated and non-tabulated data arrays
        table_data = []
        non_table_data = []
        for item in instance.feature_items.all():
            if item.column_value is None:
                non_table_data.append(item)
            else:
                table_data.append(item)

        # If a feature has tabulated data AND a description, take its lowest 
        # level FeatureItem and add it to the non-tabulated data.
        if len(table_data) > 0 and instance.desc != '[Column data]':
            first_level_gained = min(table_data, key=lambda x: x.level)
            non_table_data.append(first_level_gained)

        # serialize data and add it to representation
        representation['gained_at'] = [ClassFeatureItemSerializer(item).data for item in non_table_data]
        representation['data_for_class_table'] = [ClassFeatureColumnItemSerializer(item).data for item in table_data]

        # remove feature_items field to avoid data duplication
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

class CharacterClassSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CharacterClass
        fields = ['name', 'key', 'url']

class CharacterClassSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    features = ClassFeatureSerializer(many=True, read_only=True)
    hit_points = serializers.ReadOnlyField()
    document = DocumentSummarySerializer()
    saving_throws = AbilitySummarySerializer(many=True)
    subclass_of = CharacterClassSummarySerializer()
    
    class Meta:
        model = models.CharacterClass
        fields = '__all__'