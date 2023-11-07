"""Serializer for the FeatBenefitSerializer and FeatSerializer models."""

from rest_framework import serializers

from api_v2 import models

from .abstracts import GameContentSerializer

class CapabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Capability
        fields = ['desc']

class FeatSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    has_prerequisite = serializers.ReadOnlyField()
    capabilities = CapabilitySerializer(
        many=True)

    class Meta:
        model = models.Feat
        fields = '__all__'
