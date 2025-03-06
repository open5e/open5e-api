"""Serializers for GameSystem, License, Publisher, and Document models."""
from rest_framework import serializers
from .abstracts import GameContentSerializer

from api_v2 import models

class GameSystemSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()

    class Meta:
        model = models.GameSystem
        fields = '__all__'

class GameSystemSummarySerializer(GameContentSerializer):
    class Meta:
        model = models.GameSystem
        fields = ["name", "key"]


class LicenseSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()

    class Meta:
        model = models.License
        fields = '__all__'

class LicenseSummarySerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    class Meta:
        model = models.License
        fields = ['name', 'key']

class PublisherSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()

    class Meta:
        model = models.Publisher
        fields = '__all__'

class PublisherSummarySerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    class Meta:
        model = models.Publisher
        fields = ['name', 'key']

class DocumentSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    licenses = LicenseSummarySerializer(many=True)
    publisher = PublisherSerializer()
    gamesystem = GameSystemSerializer()

    class Meta:
        model = models.Document
        fields = '__all__'

class DocumentSummarySerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    publisher = PublisherSummarySerializer()
    gamesystem = GameSystemSummarySerializer() 
    class Meta:
        model = models.Document
        fields = ['name', 'key', 'publisher', 'gamesystem', 'permalink']