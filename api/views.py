from django.contrib.auth.models import User, Group
import django_filters
from drf_haystack.viewsets import HaystackViewSet
from rest_framework import viewsets

from api import models
from api import serializers
from api.schema_generator import CustomSchema


class ManifestViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows viewing of Manifests.

    For each data source file, there is a corresponding Manifest containing an
    md5 hash of the data inside that file. When we update our data files, the
    corresponding Manifest's hash will change. If you host a service that
    automatically downloads data from open5e, then you can periodically check
    the Manifests to see whether your data is out-of-date.
    """
    schema = CustomSchema(
        summary={
			'/manifest/': 'View Manifests',
			'/manifest/{id}/': 'View Manifest',
		},
        tags=['Manifest']
    )
    queryset = models.Manifest.objects.all()
    serializer_class = serializers.ManifestSerializer

class SearchView(HaystackViewSet):
    """
    API endpoint that allows searching our database.
    """
    schema = CustomSchema(
        summary={
			'/search/': 'Search',
			'/search/{id}/': 'Search', # I doubt this is a real endpoint
		},
        tags=['Search']
    )
    # `index_models` is an optional list of which models you would like to include
    # in the search result. You might have several models indexed, and this provides
    # a way to filter out those of no interest for this particular view.
    # (Translates to `SearchQuerySet().models(*index_models)` behind the scenes.
    serializer_class = serializers.AggregateSerializer

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = serializers.UserSerializer

class GroupViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = serializers.GroupSerializer

class DocumentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows viewing of Documents.
    """
    schema = CustomSchema(
        summary={
			'/documents/': 'View Documents',
			'/documents/{id}/': 'View Document',
		},
        tags=['Spells']
    )
    queryset = models.Document.objects.all()
    serializer_class = serializers.DocumentSerializer
    filterset_fields = (
        'slug',
        'title',
        'organization',
        'license',
        )

class SpellFilter(django_filters.FilterSet):

    class Meta:
        model = models.Spell
        fields = {
            'slug': ['in', 'iexact', 'exact', 'in', ],
            'name': ['iexact', 'exact'],
            'level': ['iexact', 'exact', 'in', ],
            'level_int': ['iexact', 'exact', 'range'],
            'school': ['iexact', 'exact', 'in', ],
            'duration': ['iexact', 'exact', 'in', ],
            'components': ['iexact', 'exact', 'in', ],
            'concentration': ['iexact', 'exact', 'in', ],
            'casting_time': ['iexact', 'exact', 'in', ],
            'dnd_class': ['iexact', 'exact', 'in', 'icontains'],
            'document__slug': ['iexact', 'exact', 'in', ],
        }

class SpellViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows viewing of Spells.
    """
    schema = CustomSchema(
        summary={
			'/spells/': 'View Spells',
			'/spells/{slug}/': 'View Spell',
		},
        tags=['Spells']
    )
    queryset = models.Spell.objects.all()
    filterset_class=SpellFilter
    serializer_class = serializers.SpellSerializer
    search_fields = ['dnd_class', 'name']
    ordering_fields = '__all__'
    ordering=['name']
    filter_fields = (
        'slug',
        'name',
        'level',
        'level_int',
        'school',
        'duration',
        'components',
        'concentration',
        'casting_time',
        'dnd_class',
        'document__slug',
    )

class MonsterViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows viewing of Monsters.
    """
    schema = CustomSchema(
        summary={
			'/monsters/': 'View Monsters',
			'/monsters/{slug}/': 'View Monster',
		},
        tags=['Monsters']
    )
    queryset = models.Monster.objects.all()
    serializer_class = serializers.MonsterSerializer
    ordering_fields = '__all__'
    ordering = ['name']
    filterset_fields = (
        'challenge_rating',
        'armor_class',
        'type',
        'name',
        'page_no',
        'document',
        'document__slug',
    )
    search_fields = ['name']

class BackgroundViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows viewing of Backgrounds.
    """
    schema = CustomSchema(
        summary={
			'/backgrounds/': 'View Backgrounds',
			'/backgrounds/{slug}/': 'View Background',
		},
        tags=['Backgrounds']
    )
    queryset = models.Background.objects.all()
    serializer_class = serializers.BackgroundSerializer
    ordering_fields = '__all__'
    ordering=['name']
    filterset_fields=(
        'name',
        'skill_proficiencies',
        'languages',
        'document__slug',
    )
    search_fields = ['name']

class PlaneViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows viewing of Planes.
    """
    schema = CustomSchema(
        summary={
			'/planes/': 'View planes',
			'/planes/{slug}/': 'View Plane',
		},
        tags=['Planes']
    )
    queryset = models.Plane.objects.all()
    serializer_class = serializers.PlaneSerializer
    filterset_fields=(
        'name',
        'document__slug',
    )

class SectionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows viewing of Sections.
    """
    schema = CustomSchema(
        summary={
			'/sections/': 'View Sections',
			'/sections/{slug}/': 'View Section',
		},
        tags=['Sections']
    )
    queryset = models.Section.objects.all()
    serializer_class = serializers.SectionSerializer
    ordering_fields = '__all__'
    ordering=['name']
    filterset_fields=(
        'name',
        'parent',
        'document__slug',
    )

class FeatViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows viewing of Feats.
    """
    schema = CustomSchema(
        summary={
			'/feats/': 'View Feats',
			'/feats/{slug}/': 'View Feat',
		},
        tags=['Feats']
    )
    queryset = models.Feat.objects.all()
    serializer_class = serializers.FeatSerializer
    filterset_fields=(
        'name',
        'prerequisite', 
        'document__slug',
        )

class ConditionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows viewing of Conditions.
    """
    schema = CustomSchema(
        summary={
			'/conditions/': 'View Conditions',
			'/conditions/{slug}/': 'View Condition',
		},
        tags=['Conditions']
    )
    queryset = models.Condition.objects.all()
    serializer_class = serializers.ConditionSerializer
    filterset_fields=(
        'name',
        'document__slug',
    )

class RaceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows viewing of Races and Subraces.
    """
    schema = CustomSchema(
        summary={
			'/races/': 'View Races',
			'/races/{slug}/': 'View Race',
		},
        tags=['Races']
    )
    queryset = models.Race.objects.all()
    serializer_class = serializers.RaceSerializer
    filterset_fields=(
        'name',
        'document__slug',
    )

class SubraceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows viewing of Races and Subraces.
    """
    schema = CustomSchema(
        summary={
			'/subraces/': 'View Subraces',
			'/subraces/{slug}/': 'View Subrace',
		},
        tags=['Subraces']
    )
    queryset = models.Subrace.objects.all()
    serializer_class = serializers.SubraceSerializer
    filterset_fields=(
        'name',
        'document__slug',
    )

class CharClassViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows viewing of Classes and Archetypes.
    """
    schema = CustomSchema(
        summary={
			'/classes/': 'View Classes',
			'/classes/{slug}/': 'View Classe',
		},
        tags=['Classes']
    )
    queryset = models.CharClass.objects.all()
    serializer_class = serializers.CharClassSerializer
    filterset_fields=(
        'name',
        'document__slug',
    )

class ArchetypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows viewing of Archetypes.
    """
    schema = CustomSchema(
        summary={
			'/archetypes/': 'View Archetypes',
			'/archetypes/{slug}/': 'View Archetype',
		},
        tags=['Archetypes']
    )
    queryset = models.Archetype.objects.all()
    serializer_class = serializers.ArchetypeSerializer
    filterset_fields=(
        'name',
        'document__slug',
    )

class MagicItemViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows viewing of Magic Items.
    """
    schema = CustomSchema(
        summary={
			'/magicitems/': 'View Magic Items',
			'/magicitems/{slug}/': 'View Magic Item',
		},
		tags=['Magic Items']
    )
    queryset = models.MagicItem.objects.all()
    serializer_class = serializers.MagicItemSerializer
    filterset_fields=(
        'name',        
        'document__slug',
    )
    search_fields = ['name']

class WeaponViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows viewing of Weapons.
    """
    schema = CustomSchema(
        summary={
			'/weapons/': 'View Weapons',
			'/weapons/{slug}/': 'View Weapon',
		},
		tags=['Weapons']
    )
    queryset = models.Weapon.objects.all()
    serializer_class = serializers.WeaponSerializer
    filterset_fields=(
        'name',        
        'document__slug',
    )
    search_fields = ['name']

class ArmorViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows viewing of Armor.
    """
    schema = CustomSchema(
        summary={
			'/armor/': 'View Armor',
			'/armor/{slug}/': 'View Armor',
		},
		tags=['Armor']
    )
    queryset = models.Armor.objects.all()
    serializer_class = serializers.ArmorSerializer
    filterset_fields=(
        'name',        
        'document__slug',
    )
    search_fields = ['name']
