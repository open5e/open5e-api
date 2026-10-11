"""Serializer for the BackgroundBenefit and Background models."""

from rest_framework import serializers

from api_v2 import models

from .abstracts import GameContentSerializer
from .document import DocumentSummarySerializer

class BackgroundBenefitSerializer(GameContentSerializer):
    # crossreferences are serialized by GameContentSerializer.get_crossreferences
    crossreferences = serializers.SerializerMethodField()

    class Meta:
        model = models.BackgroundBenefit
        fields = [
            'name',
            'desc',
            'type',
            'crossreferences'
        ]


class BackgroundSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    benefits = BackgroundBenefitSerializer(many=True)
    document = DocumentSummarySerializer()
    
    class Meta:
        model = models.Background
        fields = '__all__'
