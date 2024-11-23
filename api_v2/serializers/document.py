"""Serializers for GameSystem, License, Publisher, and Document models."""
from rest_framework import serializers
from .abstracts import GameContentSerializer

from api_v2 import models

class GameSystemSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()

    class Meta:
        model = models.GameSystem
        fields = '__all__'


class LicenseSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()

    class Meta:
        model = models.License
        fields = '__all__'


class PublisherSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()

    class Meta:
        model = models.Publisher
        fields = '__all__'


class DocumentSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    licenses = LicenseSerializer(many=True)
    publisher = PublisherSerializer()
    gamesystem = GameSystemSerializer()

    class Meta:
        model = models.Document
        fields = '__all__'