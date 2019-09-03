from django.contrib.auth.models import User, Group
from rest_framework import viewsets, filters
import django_filters
from api.models import *
from api.serializers import *
from drf_haystack.serializers import HaystackSerializer
from drf_haystack.viewsets import HaystackViewSet

from api.models import Monster
from api.search_indexes import MonsterIndex


class SearchView(HaystackViewSet):

    # `index_models` is an optional list of which models you would like to include
    # in the search result. You might have several models indexed, and this provides
    # a way to filter out those of no interest for this particular view.
    # (Translates to `SearchQuerySet().models(*index_models)` behind the scenes.
    serializer_class = AggregateSerializer


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer

class GroupViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

class DocumentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    filter_fields = (
        'slug',
        'title',
        'organization',
        'license',
        )

class SpellViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows viewing of spells.
    """
    queryset = Spell.objects.all()
    serializer_class = SpellSerializer
    search_fields = ['dnd_class', 'name']
    ordering_fields = '__all__'
    ordering=['name']
    filter_backends = (
        filters.OrderingFilter,
        django_filters.rest_framework.DjangoFilterBackend
    )
    filter_fields = (
        'level',
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
    API endpoint that allows viewing of monsters.
    """
    queryset = Monster.objects.all()
    serializer_class = MonsterSerializer
    ordering_fields = '__all__'
    ordering = ['name']
    filter_backends = (
        filters.OrderingFilter,
        django_filters.rest_framework.DjangoFilterBackend
    )
    filter_fields = (
        'challenge_rating',
        'armor_class',
        'type',
        'name',
        'document',
        'document__slug',
    )

class BackgroundViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows viewing of Backgrounds.
    """
    queryset = Background.objects.all()
    serializer_class = BackgroundSerializer
    ordering_fields = '__all__'
    ordering=['name']
    filter_backends = (
        filters.OrderingFilter,
        django_filters.rest_framework.DjangoFilterBackend
    )
    filter_fields=(
        'name',
        'skill_proficiencies',
        'languages'
        'document__slug',
    )

class PlaneViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows viewing of Planes.
    """
    queryset = Plane.objects.all()
    serializer_class = PlaneSerializer
    filter_fields=(
        'name',
        'document__slug',
    )

class SectionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows viewing of Sections.
    """
    queryset = Section.objects.all()
    serializer_class = SectionSerializer
    ordering_fields = '__all__'
    ordering=['name']
    filter_backends = (
        filters.OrderingFilter,
        django_filters.rest_framework.DjangoFilterBackend
    )
    filter_fields=(
        'name',
        'parent',
        'document__slug',
    )

class FeatViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows viewing of Feats.
    """
    queryset = Feat.objects.all()
    serializer_class = FeatSerializer
    filter_fields=('name','prerequisite', 'document__slug',)

class ConditionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows viewing of Backgrounds.
    """
    queryset = Condition.objects.all()
    serializer_class = ConditionSerializer
    filter_fields=(
        'name',
        'document__slug',
    )

class RaceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows viewing of Races and Subraces.
    """
    queryset = Race.objects.all()
    serializer_class = RaceSerializer
    filter_fields=(
        'name',
        'document__slug',
    )

class SubraceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows viewing of Races and Subraces.
    """
    queryset = Subrace.objects.all()
    serializer_class = SubraceSerializer
    filter_fields=(
        'name',
        'document__slug',
    )

class CharClassViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows viewing of Classes and Archetypes.
    """
    queryset = CharClass.objects.all()
    serializer_class = CharClassSerializer
    filter_fields=(
        'name',
        'document__slug',
    )

class ArchetypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows viewing of Archetypes.
    """
    queryset = Archetype.objects.all()
    serializer_class = ArchetypeSerializer
    filter_fields=(
        'name',
        'document__slug',
    )

class MagicItemViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows viewing of Archetypes.
    """
    queryset = MagicItem.objects.all()
    serializer_class = MagicItemSerializer
    filter_fields=(
        'name',        
        'document__slug',
    )

class WeaponViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows viewing of Archetypes.
    """
    queryset = Weapon.objects.all()
    serializer_class = WeaponSerializer
    filter_fields=(
        'name',        
        'document__slug',
    )