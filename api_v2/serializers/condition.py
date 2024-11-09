"""Serializer for the Condition model."""

from rest_framework import serializers

from api_v2 import models

from .abstracts import GameContentSerializer
from .document import DocumentSerializer

class ConditionSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    document = DocumentSerializer()

    class Meta:
        model = models.Condition
        fields = '__all__'
