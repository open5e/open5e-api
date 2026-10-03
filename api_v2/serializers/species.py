"""Serializers for the Trait and Species models."""

from rest_framework import serializers

from api_v2 import models

from .abstracts import GameContentSerializer
from .document import DocumentSummarySerializer

class SpeciesTraitSerializer(GameContentSerializer):
    # crossreferences are serialized by GameContentSerializer.get_crossreferences
    crossreferences = serializers.SerializerMethodField()
    
    class Meta:
        model = models.SpeciesTrait
        fields = ['name', 'desc', 'type', 'order', 'crossreferences']


class SpeciesSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    is_subspecies = serializers.ReadOnlyField()
    document = DocumentSummarySerializer()
    
    traits = SpeciesTraitSerializer(many=True)

    class Meta:
        model = models.Species
        fields = '__all__'

