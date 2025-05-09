"""Serializer for the Condition model."""

from rest_framework import serializers

from api_v2 import models

from .abstracts import GameContentSerializer
from .document import DocumentSummarySerializer
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
