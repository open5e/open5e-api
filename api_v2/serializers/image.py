"""Serializer for the Image model."""

from rest_framework import serializers
from .abstracts import GameContentSerializer

from api_v2 import models

class ImageSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()

    class Meta:
        model = models.Image
        fields = '__all__'
