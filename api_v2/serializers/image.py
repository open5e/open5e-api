"""Serializer for the Image model."""

from rest_framework import serializers
from .abstracts import GameContentSerializer
from .document import DocumentSummarySerializer

from api_v2 import models

class ImageSummarySerializer(GameContentSerializer):
    class Meta:
        model = models.Image
        fields = ['name', 'key', 'url', 'file_url', 'alt_text', 'attribution']

class ImageSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    file_url = serializers.ReadOnlyField()
    document = DocumentSummarySerializer()

    class Meta:
        model = models.Image
        fields = ['name', 'key', 'file_url', 'alt_text', 'attribution', 'document']
