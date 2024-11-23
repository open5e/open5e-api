"""Serializer for the DamageType model."""

from rest_framework import serializers

from api_v2 import models

from .abstracts import GameContentSerializer
from .document import DocumentSerializer

class AlignmentSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    morality = serializers.ReadOnlyField()
    societal_attitude = serializers.ReadOnlyField()
    short_name = serializers.ReadOnlyField()
    document = DocumentSerializer()
    
    class Meta:
        model = models.Alignment
        fields = '__all__'