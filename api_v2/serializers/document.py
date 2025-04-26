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
    class Meta:
        model = models.GameSystem
        fields = ['name', 'key', 'url']


class LicenseSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()

    class Meta:
        model = models.License
        fields = '__all__'

class LicenseSummarySerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    class Meta:
        model = models.License
        fields = ['name', 'key', 'url']

class PublisherSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()

    class Meta:
        model = models.Publisher
        fields = '__all__'

class PublisherSummarySerializer(serializers.ModelSerializer):
    key = serializers.ReadOnlyField()
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
    key = serializers.ReadOnlyField()
    publisher = PublisherSummarySerializer()
    gamesystem = GameSystemSummarySerializer()
    class Meta:
        model = models.Document
        fields = ['name', 'key', 'publisher', 'gamesystem', 'permalink']