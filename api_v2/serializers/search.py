"""Serializers for the SearchResult model."""

from rest_framework import serializers

from api_v2 import models

class SearchResultSerializer(serializers.ModelSerializer):
    rank = serializers.ReadOnlyField()
    text = serializers.ReadOnlyField()
    highlighted = serializers.ReadOnlyField()


    class Meta:
        model = models.SearchResult
        fields = [
            'document_pk',
            'document_name',
            'object_pk',
            'object_name',
            'object_route',
            'schema_version',
            'rank',
            'text',
            'highlighted']
