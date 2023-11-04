"""Serializer for the Language model."""

from rest_framework import serializers

from api_v2 import models

from .abstracts import GameContentSerializer

class LanguageSerializer(serializers.ModelSerializer):
    key = serializers.ReadOnlyField()
    
    class Meta:
        model = models.Language
        fields = '__all__'
