"""Serializer for the BackgroundBenefit and Background models."""

from rest_framework import serializers

from api_v2 import models

from .abstracts import GameContentSerializer
from .document import DocumentSummarySerializer

class BackgroundBenefitSerializer(GameContentSerializer):
    # crossreferences are serialized in GameContentSerializer. This delegates to parent implementation
    crossreferences = serializers.SerializerMethodField(method_name='get_crossreferences_data')
    def get_crossreferences_data(self, obj):
        return self.get_crossreferences(obj)

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
