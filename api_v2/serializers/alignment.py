"""Serializer for the DamageType model."""

from rest_framework import serializers

from api_v2 import models

from .abstracts import GameContentSerializer
from .abstracts import DescriptionSerializer
from .document import DocumentSummarySerializer

class AlignmentDescriptionSerializer(DescriptionSerializer):
    class Meta:
        model=models.AlignmentDescription
        fields=['desc','document']

class AlignmentSerializer(GameContentSerializer):

    key = serializers.ReadOnlyField()
    morality = serializers.ReadOnlyField()
    societal_attitude = serializers.ReadOnlyField()
    short_name = serializers.ReadOnlyField()
    descriptions = AlignmentDescriptionSerializer(many=True)
    document = DocumentSummarySerializer()

    class Meta:
        model = models.Alignment
        fields = [
            'key',
            'morality',
            'societal_attitude',
            'short_name',
            'descriptions',
            'document'
        ]

