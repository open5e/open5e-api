"""Serializers for the Trait and Species models."""

from rest_framework import serializers

from api_v2 import models

from .abstracts import GameContentSerializer
from .document import DocumentSummarySerializer

class SpeciesTraitSerializer(GameContentSerializer):
    # crossreferences are serialized on GameContentSerializer. This delegates to parent implementation
    crossreferences = serializers.SerializerMethodField(method_name='get_crossreferences_data')
    def get_crossreferences_data(self, obj):
        return self.get_crossreferences(obj)
    
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

