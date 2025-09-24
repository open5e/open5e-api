"""Serializer for the Condition model."""

from rest_framework import serializers

from api_v2 import models

from .abstracts import GameContentSerializer
from .abstracts import DescriptionSerializer
from .document import DocumentSummarySerializer, GameSystemSummarySerializer
from .image import ImageSummarySerializer


class ConditionDescriptionSerializer(DescriptionSerializer):
    class Meta:
        model=models.ConditionDescription
        fields=['desc','document','gamesystem']


class ConditionSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    document = DocumentSummarySerializer()
    icon = ImageSummarySerializer()
    descriptions = ConditionDescriptionSerializer(many=True)

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


class ConditionDetailSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    document = DocumentSummarySerializer()
    icon = ImageSummarySerializer()
    gamesystem_key = serializers.SerializerMethodField()
    descriptions = ConditionDescriptionSerializer(many=True)


    def get_gamesystem_key(self, obj):
        return obj.document.gamesystem.key

    class Meta:
        model = models.Condition
        fields = ['name', 'key', 'url',  'document', 'gamesystem_key', 'icon']

