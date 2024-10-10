"""Serializers for the SearchResult model."""

from rest_framework import serializers

from api_v2 import models
from api import models as v1

class SearchResultSerializer(serializers.ModelSerializer):
    """This method builds the search result object structure.
    It does a lookup based on primary keys stored in the search table.
    """
    object = serializers.SerializerMethodField(method_name='get_object')
    document = serializers.SerializerMethodField(method_name='get_document')
    route = serializers.SerializerMethodField(method_name='get_route')

    class Meta:
        model = models.SearchResult
        fields = [
            'document',
            'object_pk',
            'object_name',
            'object',
            'object_model',
            'schema_version',
            'route',
            'text',
            'highlighted']

    def get_object(self, obj):
        """This returns a given object based on the lookup from the search result key."""
        result_detail = None

        if obj.schema_version == 'v1':
            if obj.object_model == 'MagicItem':
                result_detail = v1.MagicItem.objects.get(slug=obj.object_pk)
            if obj.object_model == 'Monster':
                result_detail = v1.Monster.objects.get(slug=obj.object_pk)
            if obj.object_model == 'Spell':
                result_detail = v1.Spell.objects.get(slug=obj.object_pk)
            if obj.object_model == 'Section':
                result_detail = v1.Section.objects.get(slug=obj.object_pk)
        
        if obj.schema_version == 'v2':
            if obj.object_model == 'Item':
                result_detail = models.Item.objects.get(pk=obj.object_pk)
            if obj.object_model == 'Creature':
                result_detail = models.Creature.objects.get(pk=obj.object_pk)
            if obj.object_model == 'Spell':
                result_detail = models.Spell.objects.get(pk=obj.object_pk)
            if obj.object_model == 'CharacterClass':
                result_detail = models.CharacterClass.objects.get(pk=obj.object_pk)
            if obj.object_model == 'Race':
                result_detail = models.Race.objects.get(pk=obj.object_pk)

        if result_detail is not None:
            return result_detail.search_result_extra_fields()
        else:
            return None

    def get_document(self, obj):
        """All search results have documents related to them, this returns the related document."""
        if obj.schema_version == 'v1':
            doc = v1.Document.objects.get(slug=obj.document_pk)
            return {
                'key': doc.slug,
                'name': doc.title
                }

        if obj.schema_version == 'v2':
            doc = models.Document.objects.get(key=obj.document_pk)
            return {
                'key': doc.key,
                'name': doc.name
                }

    def get_route(self, obj):
        """Route is a way to build the link to the object."""

        route_lookup = {
            "CharacterClass":"classes",
            "CharClass":"classes",
        }

        if obj.object_model in route_lookup.keys():
            route = f"{obj.schema_version}/{route_lookup[obj.object_model]}/"
        else:
            route = f"{obj.schema_version}/{obj.object_model.lower()}s/"
        return route
