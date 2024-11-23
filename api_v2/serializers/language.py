"""Serializer for the Language model."""

from rest_framework import serializers

from api_v2 import models

from .abstracts import GameContentSerializer
from .document import DocumentSerializer

class LanguageSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    document = DocumentSerializer()
    class Meta:
        model = models.Language
        fields = '__all__'
