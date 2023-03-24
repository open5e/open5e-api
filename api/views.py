from django.contrib.auth.models import User, Group
import django_filters
from drf_haystack.viewsets import HaystackViewSet
from rest_framework.schemas.openapi import AutoSchema
from rest_framework import viewsets

from api import models
from api import serializers

class CustomSchema(AutoSchema):
    def __init__(self, **kwargs):
        self.extra_info = {
            "title": kwargs.pop("title")
        }

        super().__init__(**kwargs)

    def get_operation(self, path, method):
        # add extra_info to the operation
        oldOperation = super().get_operation(path, method)
        oldOperation['title'] = self.extra_info['title'][path]
        return oldOperation

class ManifestViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows viewing of Manifests.

    For each data source file, there is a corresponding Manifest containing an
    md5 hash of the data inside that file. When we update our data files, the
    corresponding Manifest's hash will change. If you host a service that
    automatically downloads data from open5e, then you can periodically check
    the Manifests to see whether your data is out-of-date.
    """
    queryset = models.Manifest.objects.all()
    serializer_class = serializers.ManifestSerializer

class SearchView(HaystackViewSet):
    """
    API endpoint that allows searching our database.
    """

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
    queryset = models.Document.objects.all()
    serializer_class = serializers.DocumentSerializer
    filter_fields = (
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
        title={
			'/spells/': 'View Spells',
			'/spells/{slug}/': 'View Spell',
		}
    )
    queryset = models.Spell.objects.all()
    filter_class=SpellFilter
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
        title={
			'/monsters/': 'View Monsters',
			'/monsters/{slug}/': 'View Monster',
		}
    )
    queryset = models.Monster.objects.all()
    serializer_class = serializers.MonsterSerializer
    ordering_fields = '__all__'
    ordering = ['name']
    filter_fields = (
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
        title={
			'/backgrounds/': 'View Backgrounds',
			'/backgrounds/{slug}/': 'View Background',
		}
    )
    queryset = models.Background.objects.all()
    serializer_class = serializers.BackgroundSerializer
    ordering_fields = '__all__'
    ordering=['name']
    filter_fields=(
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
        title={
			'/planes/': 'View planess',
			'/planes/{slug}/': 'View Plane',
		}
    )
    queryset = models.Plane.objects.all()
    serializer_class = serializers.PlaneSerializer
    filter_fields=(
        'name',
        'document__slug',
    )

class SectionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows viewing of Sections.
    """
    schema = CustomSchema(
        title={
			'/sections/': 'View Sections',
			'/sections/{slug}/': 'View Section',
		}
    )
    queryset = models.Section.objects.all()
    serializer_class = serializers.SectionSerializer
    ordering_fields = '__all__'
    ordering=['name']
    filter_fields=(
        'name',
        'parent',
        'document__slug',
    )

class FeatViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows viewing of Feats.
    """
    schema = CustomSchema(
        title={
			'/feats/': 'View Feats',
			'/feats/{slug}/': 'View Feat',
		}
    )
    queryset = models.Feat.objects.all()
    serializer_class = serializers.FeatSerializer
    filter_fields=('name','prerequisite', 'document__slug',)

class ConditionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows viewing of Conditions.
    """
    schema = CustomSchema(
        title={
			'/conditions/': 'View Conditions',
			'/conditions/{slug}/': 'View Condition',
		}
    )
    queryset = models.Condition.objects.all()
    serializer_class = serializers.ConditionSerializer
    filter_fields=(
        'name',
        'document__slug',
    )

class RaceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows viewing of Races and Subraces.
    """
    schema = CustomSchema(
        title={
			'/races/': 'View Races',
			'/races/{slug}/': 'View Race',
		}
    )
    queryset = models.Race.objects.all()
    serializer_class = serializers.RaceSerializer
    filter_fields=(
        'name',
        'document__slug',
    )

class SubraceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows viewing of Races and Subraces.
    """
    schema = CustomSchema(
        title={
			'/subraces/': 'View Subraces',
			'/subraces/{slug}/': 'View Subrace',
		}
    )
    queryset = models.Subrace.objects.all()
    serializer_class = serializers.SubraceSerializer
    filter_fields=(
        'name',
        'document__slug',
    )

class CharClassViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows viewing of Classes and Archetypes.
    """
    schema = CustomSchema(
        title={
			'/classes/': 'View Classes',
			'/classes/{slug}/': 'View Classe',
		}
    )
    queryset = models.CharClass.objects.all()
    serializer_class = serializers.CharClassSerializer
    filter_fields=(
        'name',
        'document__slug',
    )

class ArchetypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows viewing of Archetypes.
    """
    schema = CustomSchema(
        title={
			'/archetypes/': 'View Archetypes',
			'/archetypes/{slug}/': 'View Archetype',
		}
    )
    queryset = models.Archetype.objects.all()
    serializer_class = serializers.ArchetypeSerializer
    filter_fields=(
        'name',
        'document__slug',
    )

class MagicItemViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows viewing of Magic Items.
    """
    schema = CustomSchema(
        title={
			'/magicitems/': 'View Magic Items',
			'/magicitems/{slug}/': 'View Magic Item',
		}
    )
    queryset = models.MagicItem.objects.all()
    serializer_class = serializers.MagicItemSerializer
    filter_fields=(
        'name',
        'document__slug',
    )
    search_fields = ['name']

class WeaponViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows viewing of Weapons.
    """
    schema = CustomSchema(
        title={
			'/weapons/': 'View Weapons',
			'/weapons/{slug}/': 'View Weapon',
		}
    )
    queryset = models.Weapon.objects.all()
    serializer_class = serializers.WeaponSerializer
    filter_fields=(
        'name',
        'document__slug',
    )
    search_fields = ['name']

class ArmorViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows viewing of Armor.
    """
    schema = CustomSchema(
        title={
			'/armor/': 'View Armor',
			'/armor/{slug}/': 'View Armor',
		}
    )
    queryset = models.Armor.objects.all()
    serializer_class = serializers.ArmorSerializer
    filter_fields=(
        'name',
        'document__slug',
    )
    search_fields = ['name']
