"""Serializers for Ruleset, License, Publisher, and Document models."""
from rest_framework import serializers

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


class DocumentSerializer(serializers.HyperlinkedModelSerializer):
    key = serializers.ReadOnlyField()

    class Meta:
        model = models.Document
        fields = "__all__"