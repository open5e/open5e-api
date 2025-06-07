"""Serializer for the Condition model."""

from rest_framework import serializers

from api_v2 import models

from .abstracts import GameContentSerializer
from .document import DocumentSummarySerializer, GameSystemSummarySerializer
from .image import ImageSummarySerializer

class ConditionSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    document = DocumentSummarySerializer()
    icon = ImageSummarySerializer()

    class Meta:
        model = models.Condition
        fields = '__all__'

class ConditionSummarySerializer(GameContentSerializer):
    '''
    A slimmer ConditionSerializer, designed to serialize Condition FKs on
    other serializers. ie. The `condition_immunities` field on the Creature
    serializer. Not intended to be used directly with in a ModelViewset.
    '''
    class Meta:
        model = models.Condition
        fields = ['name', 'key', 'url']


class ConditionSystemVariantSerializer(GameContentSerializer):
    """
    Represents a condition as it exists in a specific game system/document.
    This is used within ConditionConceptSerializer to show the system-specific
    implementations of a condition concept.
    """
    key = serializers.ReadOnlyField()
    document = DocumentSummarySerializer()
    icon = ImageSummarySerializer()
    gamesystem = serializers.SerializerMethodField()
    
    def get_gamesystem(self, obj):
        return GameSystemSummarySerializer(obj.document.gamesystem).data
    
    class Meta:
        model = models.Condition
        fields = ['name', 'key', 'url', 'desc', 'document', 'gamesystem', 'icon']


class ConditionConceptSerializer(GameContentSerializer):
    """
    Serializer for the synthetic ConditionConcept model.
    This provides a unified view of equivalent conditions across game systems.
    """
    key = serializers.ReadOnlyField()
    conditions = ConditionSummarySerializer(many=True, read_only=True)
    
    class Meta:
        model = models.ConditionConcept
        fields = ['name', 'key', 'url', 'desc', 'conditions']


class ConditionConceptSummarySerializer(GameContentSerializer):
    """
    A minimal ConditionConcept serializer for use in other serializers.
    """
    class Meta:
        model = models.ConditionConcept
        fields = ['name', 'key', 'url']
