"""Serializer for the DamageType model."""

from rest_framework import serializers

from api_v2 import models

from .abstracts import GameContentSerializer
from .abstracts import DescriptionSerializer

class DamageTypeDescriptionSerializer(DescriptionSerializer):
    class Meta:
        model = models.DamageTypeDescription
        fields = ['desc','document','gamesystem']


class DamageTypeSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    descriptions = DamageTypeDescriptionSerializer(many=True)

    class Meta:
        model = models.DamageType
        fields = '__all__'

class DamageTypeSummarySerializer(GameContentSerializer):
    '''
    A slimmer DamageTypeSerializer, designed to serialize DamageType FKs on
    other serializers. Not intended to be used directly with in a ModelViewset.
    '''
    class Meta:
        model = models.DamageType
        fields = ['name', 'key']