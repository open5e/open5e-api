"""Serializers for the Trait and Race models."""

from rest_framework import serializers

from api_v2 import models

from .abstracts import GameContentSerializer

from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes

class SpellSchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SpellSchool
        fields='__all__'


class SpellCastingOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SpellCastingOption
        exclude = ['id','parent']


class SpellSerializer(GameContentSerializer):
    key = serializers.ReadOnlyField()
    slot_expended=serializers.ReadOnlyField()
    casting_options = SpellCastingOptionSerializer(many=True)
    school = SpellSchoolSerializer()

    range_unit = serializers.SerializerMethodField()
    shape_size_unit = serializers.SerializerMethodField()

    # todo: model typed as any
    @extend_schema_field(OpenApiTypes.STR)
    def get_range_unit(self, spell):
        return spell.get_range_unit()

    #todo: model typed as any
    @extend_schema_field(OpenApiTypes.STR)
    def get_shape_size_unit(self, spell):
        return spell.get_shape_size_unit()


    class Meta:
        model = models.Spell
        fields = '__all__'
