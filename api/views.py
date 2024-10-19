from django.contrib.auth.models import User, Group

from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api import models
from api import serializers
from api import filters
#from api.schema_generator import CustomSchema


class ManifestViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of of manifests.

    For each data source file, there is a corresponding manifest containing an
    MD5 hash of the data inside that file. When we update our data files, the
    corresponding manifest's hash changes. If you host a service that
    automatically downloads data from Open5e, you can periodically check
    the manifests to determine whether your data is out of date.

    retrieve: API endpoint for returning a particular manifest.

    For each data source file, there is a corresponding manifest containing an
    MD5 hash of the data inside that file. When we update our data files, the
    corresponding manifest's hash changes. If you host a service that
    automatically downloads data from Open5e, you can periodically check
    the manifests to determine whether your data is out of date.
    """
    queryset = models.Manifest.objects.all().order_by("pk")
    serializer_class = serializers.ManifestSerializer


@api_view()
def get_version(_):
    """
    API endpoint for data and api versions.
    """
    import server.version as version

    return Response({
        "DATA_V1":version.DATA_V1_HASH,
        "DATA_V2":version.DATA_V2_HASH,
        "API_V1":version.API_V1_HASH,
        "API_V2":version.API_V2_HASH
    })


# Deprecating because it's unused.
'''class SearchView(HaystackViewSet):
    """
    list: API endpoint for returning a list of search results from the Open5e database.
    """
    schema = CustomSchema(
        summary={
            '/search/': 'Search'
        },
        tags=['Search']
    )
    # `index_models` is an optional list of which models you would like to include
    # in the search result. You might have several models indexed, and this provides
    # a way to filter out those of no interest for this particular view.
    # (Translates to `SearchQuerySet().models(*index_models)` behind the scenes.

    serializer_class = serializers.AggregateSerializer
    
    def get_queryset(self, *args, **kwargs):
        queryset = super().get_queryset(*args, **kwargs)
        if not self.request.GET.get('text'):
            # Blank text should return results. Improbable query below.
            return queryset.filter(wisdom="99999")
        return queryset
'''


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
    list: API endpoint for returning a list of documents.
    retrieve: API endpoint for returning a particular document.
    """
    queryset = models.Document.objects.all().order_by("pk")
    serializer_class = serializers.DocumentSerializer
    search_fields = ['title', 'desc']
    filterset_fields = (
        'slug',
        'title',
        'organization',
        'license',
        )


class SpellViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of spells.
    retrieve: API endpoint for returning a particular spell.
    """
    queryset = models.Spell.objects.all().order_by("pk")
    filterset_class=filters.SpellFilter
    serializer_class = serializers.SpellSerializer
    search_fields = ['dnd_class', 'name', 'desc']
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


class SpellListViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of spell lists.
    retrieve: API endpoint for returning a particular spell list.
    """
    queryset = models.SpellList.objects.all().order_by("pk")
    serializer_class = serializers.SpellListSerializer
    filterset_class = filters.SpellListFilter
    search_fields = ['name', 'desc']


class MonsterViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of monsters.
    retrieve: API endpoint for returning a particular monster.
    """
    queryset = models.Monster.objects.all().order_by("pk")
    filterset_class = filters.MonsterFilter
    
    serializer_class = serializers.MonsterSerializer
    search_fields = ['name', 'desc']

class BackgroundViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of backgrounds.
    retrieve: API endpoint for returning a particular background.
    """
    queryset = models.Background.objects.all().order_by("pk")
    serializer_class = serializers.BackgroundSerializer
    ordering_fields = '__all__'
    ordering = ['name']
    filterset_class = filters.BackgroundFilter
    search_fields = ['name', 'desc']


class PlaneViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of planes.
    retrieve: API endpoint for returning a particular plane.
    """
    queryset = models.Plane.objects.all().order_by("pk")
    serializer_class = serializers.PlaneSerializer
    filterset_class = filters.PlaneFilter
    search_fields = ['name', 'desc']


class SectionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of sections.
    retrieve: API endpoint for returning a particular section.
    """
    queryset = models.Section.objects.all().order_by("pk")
    serializer_class = serializers.SectionSerializer
    ordering_fields = '__all__'
    ordering=['name']
    filterset_class = filters.SectionFilter
    search_fields = ['name', 'desc']


class FeatViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of feats.
    retrieve: API endpoint for returning a particular feat.
    """
    queryset = models.Feat.objects.all().order_by("pk")
    serializer_class = serializers.FeatSerializer
    filterset_class = filters.FeatFilter
    search_fields = ['name', 'desc']


class ConditionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of conditions.
    retrieve: API endpoint for returning a particular condition.
    """
    queryset = models.Condition.objects.all().order_by("pk")
    serializer_class = serializers.ConditionSerializer
    search_fields = ['name', 'desc']
    filterset_class = filters.ConditionFilter


class RaceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of races.
    retrieve: API endpoint for returning a particular race.
    """
    queryset = models.Race.objects.all().order_by("pk")
    serializer_class = serializers.RaceSerializer
    filterset_class = filters.RaceFilter
    search_fields = ['name', 'desc']


class SubraceViewSet(viewsets.ReadOnlyModelViewSet):
    # Unused, but could be implemented later.
    """
    list: API endpoint that allows viewing of Subraces.
    retrieve: API endpoint for returning a particular subrace.
    """
    queryset = models.Subrace.objects.all().order_by("pk")
    serializer_class = serializers.SubraceSerializer
    search_fields = ['name', 'desc']
    filterset_fields=(
        'name',
        'document__slug',
    )


class CharClassViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of classes and archetypes.
    retrieve: API endpoint for returning a particular class or archetype.
    """
    queryset = models.CharClass.objects.all().order_by("pk")
    serializer_class = serializers.CharClassSerializer
    filterset_class = filters.CharClassFilter
    search_fields = ['name', 'desc']


class ArchetypeViewSet(viewsets.ReadOnlyModelViewSet):
    # Unused but could be implemented later.
    """
    list: API endpoint that allows viewing of Archetypes.
    retrieve: API endpoint for returning a particular archetype.
    """
    queryset = models.Archetype.objects.all().order_by("pk")
    serializer_class = serializers.ArchetypeSerializer
    search_fields = ['name', 'desc']
    filterset_fields=(
        'name',
        'document__slug',
    )


class MagicItemViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of magic items.
    retrieve: API endpoint for returning a particular magic item.
    """
    queryset = models.MagicItem.objects.all().order_by("pk")
    serializer_class = serializers.MagicItemSerializer
    filterset_class = filters.MagicItemFilter
    search_fields = ['name', 'desc']


class WeaponViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of weapons.
    retrieve: API endpoint for returning a particular weapon.
    """
    queryset = models.Weapon.objects.all().order_by("pk")
    serializer_class = serializers.WeaponSerializer
    filterset_class = filters.WeaponFilter
    search_fields = ['name', 'desc']


class ArmorViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of armor.
    retrieve: API endpoint for returning a particular armor.
    """
    queryset = models.Armor.objects.all().order_by("pk")
    serializer_class = serializers.ArmorSerializer
    filterset_class = filters.ArmorFilter
    search_fields = ['name', 'desc']
