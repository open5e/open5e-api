"""Serializers for GameSystem, License, Publisher, and Document models."""
from rest_framework import serializers
from .abstracts import GameContentSerializer

from api_v2 import models

class GameSystemSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()

    class Meta:
        model = models.GameSystem
        fields = '__all__'

class GameSystemSummarySerializer(serializers.ModelSerializer):
    '''
    A slimmer GameSystemSerializer, designed to serialize GameSystem FKs on 
    other serializers. Not intended to be used directly with in a ModelViewset.
    '''
    class Meta:
        model = models.GameSystem
        fields = ['name', 'key', 'url']


class LicenseSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()

    class Meta:
        model = models.License
        fields = '__all__'

class LicenseSummarySerializer(GameContentSerializer):
    '''
    A slimmer LicenseSerializer, designed to serialize License FKs on other 
    serializers. Not intended to be used directly with in a ModelViewset.
    '''
    class Meta:
        model = models.License
        fields = ['name', 'key', 'url']

class PublisherSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()

    class Meta:
        model = models.Publisher
        fields = '__all__'

class PublisherSummarySerializer(serializers.ModelSerializer):
    '''
    A slimmer PublisherSerializer, designed to serialize Publisher FKs on other
    serializers. Not intended to be used directly with in a ModelViewset.
    '''
    class Meta:
        model = models.Publisher
        fields = ['name', 'key', 'url']

class DocumentSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    licenses = LicenseSummarySerializer(read_only=True, many=True)
    publisher = PublisherSummarySerializer(read_only=True)
    gamesystem = GameSystemSummarySerializer(read_only=True)

    class Meta:
        model = models.Document
        fields = '__all__'

class DocumentSummarySerializer(GameContentSerializer):
    '''
    A slimmer DocumentSerializer, designed to serialize Documents FKs on other
    serializers. Not intended to be used directly with in a ModelViewset.
    '''
    publisher = PublisherSummarySerializer()
    gamesystem = GameSystemSummarySerializer()

    class Meta:
        model = models.Document
        fields = ['name', 'key', 'publisher', 'gamesystem', 'permalink']