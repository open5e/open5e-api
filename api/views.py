from django.contrib.auth.models import User, Group
import django_filters
from drf_haystack.viewsets import HaystackViewSet
from rest_framework import viewsets

from api import models
from api import serializers
from api.schema_generator import CustomSchema


class ManifestViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for returning a list of of manifests.

    For each data source file, there is a corresponding manifest containing an
    MD5 hash of the data inside that file. When we update our data files, the
    corresponding manifest's hash changes. If you host a service that
    automatically downloads data from Open5e, you can periodically check
    the manifests to determine whether your data is out of date.
    """
    schema = CustomSchema(
        summary={
			'/manifest/': 'List Manifests',
			'/manifest/{id}/': 'Retrieve Manifest',
		},
        tags=['Manifests']
    )
    queryset = models.Manifest.objects.all()
    serializer_class = serializers.ManifestSerializer

class SearchView(HaystackViewSet):
    """
    API endpoint for returning a list of search results from the Open5e database.
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
    API endpoint for returning a list of documents.
    """
    schema = CustomSchema(
        summary={
			'/documents/': 'List Documents',
			'/documents/{id}/': 'Retrieve Document',
		},
        tags=['Documents'],
        query={
			'slug': 'A short, human readable string uniquely identifying this document',
			'title': 'A short descriptive title of this document',
			'organization': 'The organization that published the document',
			'license': 'The license under which the document is published',
		}
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
    API endpoint for returning a list of spells.
    """
    schema = CustomSchema(
        summary={
			'/spells/': 'List Spells',
			'/spells/{slug}/': 'Retrieve Spell',
		},
        tags=['Spells']
    )
    queryset = models.Spell.objects.all()
    filterset_class=SpellFilter
    serializer_class = serializers.SpellSerializer
    search_fields = ['dnd_class', 'name']
    ordering_fields = '__all__'
    ordering=['name']
    filterset_fields = (
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
    API endpoint for returning a list of monsters.
    """
    schema = CustomSchema(
        summary={
			'/monsters/': 'List Monsters',
			'/monsters/{slug}/': 'Retrieve Monster',
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
    API endpoint for returning a list of backgrounds.
    """
    schema = CustomSchema(
        summary={
			'/backgrounds/': 'List Backgrounds',
			'/backgrounds/{slug}/': 'Retrieve Background',
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
    API endpoint for returning a list of planes.
    """
    schema = CustomSchema(
        summary={
			'/planes/': 'List Planes',
			'/planes/{slug}/': 'Retrieve Plane',
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
    API endpoint for returning a list of sections.
    """
    schema = CustomSchema(
        summary={
			'/sections/': 'List Sections',
			'/sections/{slug}/': 'Retrieve Section',
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
    API endpoint for returning a list of feats.
    """
    schema = CustomSchema(
        summary={
			'/feats/': 'List Feats',
			'/feats/{slug}/': 'Retrieve Feat',
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
    API endpoint for returning a list of conditions.
    """
    schema = CustomSchema(
        summary={
			'/conditions/': 'List Conditions',
			'/conditions/{slug}/': 'Retrieve Condition',
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
    API endpoint for returning a list of races and subraces.
    """
    schema = CustomSchema(
        summary={
			'/races/': 'List Races',
			'/races/{slug}/': 'Retrieve Race',
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
			'/subraces/': 'List Subraces',
			'/subraces/{slug}/': 'Retrieve Subrace',
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
    API endpoint for returning a list of classes and archetypes.
    """
    schema = CustomSchema(
        summary={
			'/classes/': 'List Classes',
			'/classes/{slug}/': 'Retrieve Class',
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
			'/archetypes/': 'List Archetypes',
			'/archetypes/{slug}/': 'Retrieve Archetype',
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
    API endpoint for returning a list of magic items.
    """
    schema = CustomSchema(
        summary={
			'/magicitems/': 'List Magic Items',
			'/magicitems/{slug}/': 'Retrieve Magic Item',
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
    API endpoint for returning a list of weapons.
    """
    schema = CustomSchema(
        summary={
			'/weapons/': 'List Weapons',
			'/weapons/{slug}/': 'Retrieve Weapon',
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
    API endpoint for returning a list of armor.
    """
    schema = CustomSchema(
        summary={
			'/armor/': 'List Armor',
			'/armor/{slug}/': 'Retrieve Armor',
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
