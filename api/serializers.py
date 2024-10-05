from django.contrib.auth.models import User, Group
from rest_framework import serializers

from api import models
from api import search_indexes


class ManifestSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Manifest
        fields = ('filename', 'type', 'hash', 'created_at')

class DynamicFieldsModelSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        # Instantiate the superclass normally
        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

        # The request doesn't exist when generating an OAS file, so we have to check that first
        if 'request' in self.context:
            fields = self.context['request'].query_params.get('fields')
            if fields:
                fields = fields.split(',')
                # Drop any fields that are not specified in the `fields` argument.
                allowed = set(fields)
                existing = set(self.fields.keys())
                for field_name in existing - allowed:
                    self.fields.pop(field_name)

class DynamicFieldsHyperlinkedModelSerializer(
    DynamicFieldsModelSerializer, serializers.HyperlinkedModelSerializer
    ):
    """Abstract base class to be inherited by Serializers that both use
    dynamic fields as well as hyperlinked relationships."""
    pass

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'groups')

class DocumentSerializer(DynamicFieldsHyperlinkedModelSerializer):
    class Meta:
            model = models.Document
            fields = (
                'title',
                'slug',
                'url',
                'license',
                'desc',
                'license',
                'author',
                'organization',
                'version',
                'copyright',
                'license_url',)

class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')

class MonsterSerializer(DynamicFieldsHyperlinkedModelSerializer):
    
    speed = serializers.SerializerMethodField()
    environments = serializers.SerializerMethodField()
    skills = serializers.SerializerMethodField()
    actions = serializers.SerializerMethodField()
    bonus_actions = serializers.SerializerMethodField()
    reactions = serializers.SerializerMethodField()
    legendary_actions = serializers.SerializerMethodField()
    special_abilities = serializers.SerializerMethodField()
    img_main = serializers.SerializerMethodField()

    def get_img_main(self, monster):
        request = self.context.get('request')
        domain = str(request.get_host())
        img_url = monster.img_main
        if img_url != None:
            return ('http://{domain}/{path}'.format(domain=domain, path=img_url))
        else:
             return None

    def get_speed(self, monster):
        return monster.speed()

    def get_environments(self, monster):
        return monster.environments()

    def get_skills(self, monster):
        return monster.skills()

    def get_actions(self, monster):
        return monster.actions()
    
    def get_bonus_actions(self, monster):
        return monster.bonus_actions()

    def get_reactions(self, monster):
        return monster.reactions()

    def get_legendary_actions(self, monster):
        return monster.legendary_actions()

    def get_special_abilities(self, monster):
        return monster.special_abilities()


    class Meta:
        model = models.Monster
        fields = (
            'slug',
            'desc',
            'name',
            'size',
            'type',
            'subtype',
            'group',
            'alignment',
            'armor_class',
            'armor_desc',
            'hit_points',
            'hit_dice',
            'speed',
            'strength',
            'dexterity',
            'constitution',
            'intelligence',
            'wisdom',
            'charisma',
            'strength_save',
            'dexterity_save',
            'constitution_save',
            'intelligence_save',
            'wisdom_save',
            'charisma_save',
            'perception',
            'skills',
            'damage_vulnerabilities',
            'damage_resistances',
            'damage_immunities',
            'condition_immunities',
            'senses',
            'languages',
            'challenge_rating',
            'cr',
            'actions',
            'bonus_actions',
            'reactions',
            'legendary_desc',
            'legendary_actions',
            'special_abilities',
            'spell_list',
            'page_no',
            'environments',
            'img_main',
            'document__slug',
            'document__title',
            'document__license_url',
            'document__url'
        )

class SpellSerializer(DynamicFieldsModelSerializer):

    ritual = serializers.CharField(source='v1_ritual')
    level_int = serializers.IntegerField(source='spell_level')
    level = serializers.CharField(source='v1_level')
    concentration = serializers.CharField(source='v1_concentration')
    components = serializers.CharField(source='v1_components')

    class Meta:
        model = models.Spell
        fields = (
            'slug',
            'name',
            'desc',
            'higher_level',
            'page',
            'range',
            'target_range_sort',
            'components',
            'requires_verbal_components',
            'requires_somatic_components',
            'requires_material_components',
            'material',
            'can_be_cast_as_ritual',
            'ritual',
            'duration',
            'concentration',
            'requires_concentration',
            'casting_time',
            'level',
            'level_int',
            'spell_level',
            'school',
            'dnd_class',
            'spell_lists',
            'archetype',
            'circles',
            'document__slug',
            'document__title',
            'document__license_url',
            'document__url'
        )

class SpellListSerializer(DynamicFieldsModelSerializer):
    #spells = SpellSerializer(many=True, read_only=True, context={'request': ''}) #Passing a blank request.
    class Meta:
        model = models.SpellList
        fields = (
            'slug',
            'name',
            'desc',
            'spells',
            'document__slug',
            'document__title',
            'document__license_url',
            'document__url'
        )

class BackgroundSerializer(DynamicFieldsHyperlinkedModelSerializer):
    class Meta:
        model = models.Background
        fields = (
            'name',
            'desc',
            'slug',
            'skill_proficiencies',
            'tool_proficiencies',
            'languages',
            'equipment',
            'feature',
            'feature_desc',
            'suggested_characteristics',
            'document__slug',
            'document__title',
            'document__license_url',
            'document__url'
        )

class PlaneSerializer(DynamicFieldsHyperlinkedModelSerializer):
    class Meta:
        model = models.Plane
        fields = ('slug','name','desc','document__slug', 'document__title', 'document__url','parent')

class SectionSerializer(DynamicFieldsHyperlinkedModelSerializer):
    class Meta:
        model = models.Section
        fields = (
            'slug',
            'name',
            'desc',
            'document__slug',
            'document__title',
            'document__license_url',
            'document__url',
            'parent'
        )

class FeatSerializer(DynamicFieldsHyperlinkedModelSerializer):
    class Meta:
        model = models.Feat
        fields = (
            'slug',
            'name',
            'desc',
            'prerequisite',
            'effects_desc',
            'document__slug',
            'document__title',
            'document__url'
        )

class ConditionSerializer(DynamicFieldsHyperlinkedModelSerializer):
    class Meta:
        model = models.Condition
        fields = (
            'slug',
            'name',
            'desc',
            'document__slug',
            'document__title',
            'document__url'
        )

class SubraceSerializer(DynamicFieldsHyperlinkedModelSerializer):
    class Meta:
        model = models.Subrace
        fields = ('name',
        'slug',
        'desc',
        'asi',
        'traits',
        'asi_desc',
        'document__slug',
        'document__title',
        'document__url'
    )

class RaceSerializer(DynamicFieldsHyperlinkedModelSerializer):
    subraces = SubraceSerializer(many=True,read_only=True)
    class Meta:
        model = models.Race
        fields = (
            'name',
            'slug',
            'desc',
            'asi_desc',
            'asi',
            'age',
            'alignment',
            'size',
            'size_raw',
            'speed',
            'speed_desc',
            'languages',
            'vision',
            'traits',
            'subraces',
            'document__slug',
            'document__title',
            'document__license_url',
            'document__url'
        )

class ArchetypeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Archetype
        fields = (
            'name',
            'slug',
            'desc',
            'document__slug',
            'document__title',
            'document__license_url',
            'document__url'
        )

class CharClassSerializer(DynamicFieldsHyperlinkedModelSerializer):
    archetypes = ArchetypeSerializer(many=True,read_only=True)
    class Meta:
        model = models.CharClass
        fields = (
            'name',
            'slug',
            'desc',
            'hit_dice',
            'hp_at_1st_level',
            'hp_at_higher_levels',
            'prof_armor',
            'prof_weapons',
            'prof_tools',
            'prof_saving_throws',
            'prof_skills',
            'equipment',
            'table',
            'spellcasting_ability',
            'subtypes_name',
            'archetypes',
            'document__slug',
            'document__title',
            'document__license_url',
            'document__url'
        )

class MagicItemSerializer(DynamicFieldsHyperlinkedModelSerializer):
    class Meta:
        model = models.MagicItem
        fields = (
            'slug',
            'name',
            'type',
            'desc',
            'rarity',
            'requires_attunement',
            'document__slug',
            'document__title',
            'document__url'
        )

class WeaponSerializer(DynamicFieldsHyperlinkedModelSerializer):
    class Meta:
        model = models.Weapon
        fields = (
            'name',
            'slug',
            'category',
            'document__slug',
            'document__title',
            'document__license_url',
            'document__url',
            'cost',
            'damage_dice',
            'damage_type',
            'weight',
            'properties')

class ArmorSerializer(DynamicFieldsHyperlinkedModelSerializer):
    class Meta:
        model = models.Armor
        fields = (
            'name',
            'slug',
            'category',
            'document__slug',
            'document__title',
            'document__license_url',
            'document__url',
            'base_ac',
            'plus_dex_mod',
            'plus_con_mod',
            'plus_wis_mod',
            'plus_flat_mod',
            'plus_max',
            'ac_string',
            'strength_requirement',
            'cost',
            'weight',
            'stealth_disadvantage')

# Deprecating because it's unused.
'''class AggregateSerializer(HighlighterMixin, HaystackSerializer):

    class Meta:
        index_classes = [search_indexes.MonsterIndex, 
            search_indexes.SpellIndex, 
            search_indexes.SectionIndex, 
            search_indexes.ConditionIndex, 
            search_indexes.CharClassIndex, 
            search_indexes.RaceIndex,
            search_indexes.MagicItemIndex,]
        fields = ['name',
            'text',
            'route',
            'slug',
            'level',
            'school',
            'dnd_class',
            'ritual',
            'armor_class',
            'hit_points',
            'hit_dice',
            'challenge_rating',
            'strength',
            'dexterity',
            'constitution',
            'intelligence',
            'wisdom',
            'charisma',
            'rarity',
            'type',
            'source',
            'requires_attunement',
            'document_slug',
            'document_title',
            'parent',
        ]
'''