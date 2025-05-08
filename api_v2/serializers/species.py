"""Serializers for the Trait and Species models."""

from rest_framework import serializers

from api_v2 import models

from .abstracts import GameContentSerializer
from .document import DocumentSummarySerializer

class SpeciesTraitSerializer(GameContentSerializer):

    class Meta:
        model = models.SpeciesTrait
        fields = ['name', 'desc']


class SpeciesSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    is_subspecies = serializers.ReadOnlyField()
    document = DocumentSummarySerializer()
    
    traits = SpeciesTraitSerializer(many=True)

    class Meta:
        model = models.Species
        fields = '__all__'

