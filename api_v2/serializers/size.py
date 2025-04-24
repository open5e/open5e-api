"""Serializer for the Size model."""

from rest_framework import serializers

from api_v2 import models

from .abstracts import GameContentSerializer
from .document import DocumentSummarySerializer
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes

class SizeSerializer(GameContentSerializer):
    """Serializer for the Size type"""
    key = serializers.ReadOnlyField()
    document = DocumentSummarySerializer()
    distance_unit = serializers.SerializerMethodField()

    class Meta:
        model = models.Size
        fields = '__all__'
    
    # todo: model typed as any
    @extend_schema_field(OpenApiTypes.STR)
    def get_distance_unit(self, Size):
        return Size.get_distance_unit
