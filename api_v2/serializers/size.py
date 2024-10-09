"""Serializer for the Size model."""

from rest_framework import serializers

from api_v2 import models

from .abstracts import GameContentSerializer

class SizeSerializer(GameContentSerializer):
    """Serializer for the Size type"""
    key = serializers.ReadOnlyField()
    distance_unit = serializers.SerializerMethodField()

    class Meta:
        model = models.Size
        fields = '__all__'
    
    def get_distance_unit(self, Size):
        return Size.get_distance_unit
