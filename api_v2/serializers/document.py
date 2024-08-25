"""Serializers for Ruleset, License, Publisher, and Document models."""
from rest_framework import serializers
from .abstracts import GameContentSerializer

from api_v2 import models

class RulesetSerializer(serializers.HyperlinkedModelSerializer):
    key = serializers.ReadOnlyField()

    class Meta:
        model = models.Ruleset
        fields = '__all__'


class LicenseSerializer(serializers.HyperlinkedModelSerializer):
    key = serializers.ReadOnlyField()

    class Meta:
        model = models.License
        fields = '__all__'


class PublisherSerializer(serializers.HyperlinkedModelSerializer):
    key = serializers.ReadOnlyField()

    class Meta:
        model = models.Publisher
        fields = '__all__'


class DocumentSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    stats = serializers.ReadOnlyField()
    publisher_name = serializers.SerializerMethodField()
    publisher_key = serializers.SerializerMethodField()
    ruleset_name = serializers.SerializerMethodField()
    ruleset_key = serializers.SerializerMethodField()

    def get_publisher_name(self, obj):
        return obj.publisher.name if obj.publisher else None

    def get_publisher_key(self, obj):
        return obj.publisher.key if obj.publisher else None
    
    def get_publisher_name(self, obj):
        return obj.publisher.name if obj.publisher else None

    def get_publisher_key(self, obj):
        return obj.publisher.key if obj.publisher else None
    
    def get_ruleset_name(self, obj):
        return obj.ruleset.name if obj.ruleset else None

    def get_ruleset_key(self, obj):
        return obj.ruleset.key if obj.ruleset else None
    
    class Meta:
        model = models.Document
        fields = '__all__'