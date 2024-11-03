"""Serializer for the FeatBenefitSerializer and FeatSerializer models."""

from rest_framework import serializers

from api_v2 import models

from .abstracts import GameContentSerializer
from .document import DocumentSerializer

class FeatBenefitSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.FeatBenefit
        fields = ['desc']

class FeatSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    has_prerequisite = serializers.ReadOnlyField()
    benefits = FeatBenefitSerializer(
        many=True)
    document = DocumentSerializer()

    class Meta:
        model = models.Feat
        fields = '__all__'
