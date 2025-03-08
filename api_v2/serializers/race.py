"""Serializers for the Trait and Race models."""

from rest_framework import serializers

from api_v2 import models

from .abstracts import GameContentSerializer
from .document import DocumentSummarySerializer

class RaceTraitSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.RaceTrait
        fields = ['name', 'desc']


class RaceSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    is_subrace = serializers.ReadOnlyField()
    document = DocumentSummarySerializer()
    
    traits = RaceTraitSerializer(many=True)

    class Meta:
        model = models.Race
        fields = '__all__'

