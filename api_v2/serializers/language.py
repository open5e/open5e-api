"""Serializer for the Language model."""

from rest_framework import serializers

from api_v2 import models

from .abstracts import GameContentSerializer
from .document import DocumentSummarySerializer

class LanguageSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    document = DocumentSummarySerializer()
    class Meta:
        model = models.Language
        fields = '__all__'

class LanguageSummarySerializer(GameContentSerializer):
    """
    This serializer is used for FKs to the Language model from other 
    serializers. ie. for the languages spoken by creatures on the 
    CreatureSerializer.
    """
    key = serializers.ReadOnlyField()
    class Meta:
        model = models.Language
        fields = ['name', 'key', 'url', 'desc']