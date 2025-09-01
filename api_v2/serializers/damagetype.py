"""Serializer for the DamageType model."""

from rest_framework import serializers

from api_v2 import models

from .abstracts import GameContentSerializer

class DamageTypeSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    desc = serializers.SerializerMethodField()

    class Meta:
        model = models.DamageType
        fields = '__all__'

    def get_desc(self, DamageType):
        return DamageType.get_desc.desc


class DamageTypeSummarySerializer(GameContentSerializer):
    '''
    A slimmer DamageTypeSerializer, designed to serialize DamageType FKs on
    other serializers. Not intended to be used directly with in a ModelViewset.
    '''
    class Meta:
        model = models.DamageType
        fields = ['name', 'key', 'url']