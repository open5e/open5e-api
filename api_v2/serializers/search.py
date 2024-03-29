"""Serializers for the SearchResult model."""

from rest_framework import serializers

from api_v2 import models
from api import models as v1

class SearchResultSerializer(serializers.ModelSerializer):
    rank = serializers.ReadOnlyField()
    text = serializers.ReadOnlyField()
    highlighted = serializers.ReadOnlyField()
    object = serializers.SerializerMethodField(method_name='get_object')


    class Meta:
        model = models.SearchResult
        fields = [
            'document_pk',
            'document_name',
            'object_pk',
            'object_name',
            'object',
            'object_route',
            'schema_version',
            'rank',
            'text',
            'highlighted']

    def get_object(self, obj):
        if obj.schema_version == 'v1':
            if obj.object_route == 'magicitems/':
                result_detail = v1.MagicItem.objects.get(slug=obj.object_pk)
                return result_detail.search_result_extra_fields()
                
            if obj.object_route == 'monsters/':
                result_detail = v1.Monster.objects.get(slug=obj.object_pk)
                return result_detail.search_result_extra_fields()
                
            if obj.object_route == 'spells/':
                result_detail = v1.Spell.objects.get(slug=obj.object_pk)
                return result_detail.search_result_extra_fields()

            if obj.object_route == 'sections/':
                result_detail = v1.Section.objects.get(slug=obj.object_pk)
                return result_detail.search_result_extra_fields()