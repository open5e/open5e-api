from django.contrib.auth.models import User, Group
import django_filters
from drf_haystack.viewsets import HaystackViewSet
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api import models
from api import serializers
from api.schema_generator import CustomSchema


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
    schema = CustomSchema(
        summary={
            '/manifest/': 'List Manifests',
            '/manifest/{id}/': 'Retrieve Manifest',
        },
        tags=['Manifests'],
    )
    queryset = models.Manifest.objects.all()
    serializer_class = serializers.ManifestSerializer


@api_view()
def get_version(request):
    import version
    return Response({"GIT_REF":version.GIT_REF, "BUILD_ID":version.BUILD_ID})


class SearchView(HaystackViewSet):
    """
    list: API endpoint for returning a list of search results from the Open5e database.
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
    list: API endpoint for returning a list of documents.
    retrieve: API endpoint for returning a particular document.
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
		})
    queryset = models.Document.objects.all()
    serializer_class = serializers.DocumentSerializer
    filterset_fields = (
        'slug',
        'title',
        'organization',
        'license',
        )

class SpellFilter(django_filters.FilterSet):
    level_int = django_filters.NumberFilter(field_name='spell_level')
    concentration = django_filters.CharFilter(field_name='concentration')
    components = django_filters.CharFilter(field_name='components')
    spell_lists_not = django_filters.CharFilter(field_name='spell_lists', exclude=True)

    class Meta:
        model = models.Spell
        fields = {
            'slug': ['in', 'iexact', 'exact', 'in', ],
            'name': ['iexact', 'exact'],
            'spell_level': ['exact', 'range', 'gt', 'gte', 'lt', 'lte'],
            'target_range_sort': ['exact', 'range', 'gt', 'gte', 'lt', 'lte'],
            'school': ['iexact', 'exact', 'in', ],
            'duration': ['iexact', 'exact', 'in', ],
            'requires_concentration': ['exact'],
            'requires_verbal_components': ['exact'],
            'requires_somatic_components': ['exact'],
            'requires_material_components': ['exact'],
            'casting_time': ['iexact', 'exact', 'in', ],
            'dnd_class': ['iexact', 'exact', 'in', 'icontains'],
            'spell_lists' : ['exact'],
            'document__slug': ['iexact', 'exact', 'in', ]
        }

class SpellViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of spells.
    retrieve: API endpoint for returning a particular spell.
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

class SpellListFilter(django_filters.FilterSet):

    class Meta:
        model = models.SpellList
        fields = {
            'slug': ['in', 'iexact', 'exact', 'in', ],
            'name': ['iexact', 'exact'],
            'desc': ['iexact', 'exact', 'in', 'icontains'],
            'document__slug': ['iexact', 'exact', 'in', ]
        }


class SpellListViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of spell lists.
    retrieve: API endpoint for returning a particular spell list.
    """
    schema = CustomSchema(
        summary={
            '/spelllist/': 'List Spell Lists',
            '/spelllist/{slug}/': 'Retrieve Spell List',
        },
        tags=['SpellList']
    )
    queryset = models.SpellList.objects.all()
    serializer_class = serializers.SpellListSerializer
    filterset_class = SpellListFilter

class MonsterFilter(django_filters.FilterSet):

    class Meta:
        model = models.Monster
        fields = {
            'slug': ['in', 'iexact', 'exact', 'in', ],
            'name': ['iexact', 'exact'],
            'desc': ['iexact', 'exact', 'in', 'icontains'],
            'cr': ['exact', 'range', 'gt', 'gte', 'lt', 'lte'],
            'armor_class': ['exact', 'range', 'gt', 'gte', 'lt', 'lte'],
            'type': ['iexact', 'exact', 'in', 'icontains'],
            'name': ['iexact', 'exact'],
            'page_no': ['exact', 'range', 'gt', 'gte', 'lt', 'lte'],
            'document__slug': ['iexact', 'exact', 'in', ]
        }

class MonsterViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of monsters.
    retrieve: API endpoint for returning a particular monster.
    """
    schema = CustomSchema(
        summary={
            '/monsters/': 'List Monsters',
            '/monsters/{slug}/': 'Retrieve Monster',
        },
        tags=['Monsters']
    )
    queryset = models.Monster.objects.all()
    filterset_class = MonsterFilter
    
    serializer_class = serializers.MonsterSerializer
    search_fields = ['name']

class BackgroundFilter(django_filters.FilterSet):

    class Meta:
        model = models.Background
        fields = {
            'slug': ['in', 'iexact', 'exact', 'in', ],
            'name': ['iexact', 'exact'],
            'skill_proficiencies': ['iexact', 'exact', 'icontains'],
            'tool_proficiencies': ['iexact', 'exact', 'icontains'],
            'languages': ['iexact', 'exact', 'icontains'],
            'feature': ['iexact', 'exact', 'icontains'],
            'feature_desc': ['iexact', 'exact', 'icontains'],
            'desc': ['iexact', 'exact', 'in', 'icontains'],
            'document__slug': ['iexact', 'exact', 'in', ]
        }

class BackgroundViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of backgrounds.
    retrieve: API endpoint for returning a particular background.
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
    ordering = ['name']
    filterset_class = BackgroundFilter
    search_fields = ['name']

class PlaneFilter(django_filters.FilterSet):

    class Meta:
        model = models.Plane
        fields = {
            'slug': ['in', 'iexact', 'exact', 'in', ],
            'name': ['iexact', 'exact'],
            'desc': ['iexact', 'exact', 'in', 'icontains'],
            'document__slug': ['iexact', 'exact', 'in', ]
        }

class PlaneViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of planes.
    retrieve: API endpoint for returning a particular plane.
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
    filterset_class=PlaneFilter

class SectionFilter(django_filters.FilterSet):

    class Meta:
        model = models.Section
        fields = {
            'slug': ['in', 'iexact', 'exact', 'in', ],
            'name': ['iexact', 'exact'],
            'desc': ['iexact', 'exact', 'in', 'icontains'],
            'parent' : ['iexact', 'exact', 'in', 'icontains'],
            'document__slug': ['iexact', 'exact', 'in', ]
        }

class SectionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of sections.
    retrieve: API endpoint for returning a particular section.
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
    filterset_class = SectionFilter

class FeatFilter(django_filters.FilterSet):

    class Meta:
        model = models.Feat
        fields = {
            'slug': ['in', 'iexact', 'exact', 'in', ],
            'name': ['iexact', 'exact'],
            'desc': ['iexact', 'exact', 'in', 'icontains'],
            'document__slug': ['iexact', 'exact', 'in']
        }

class FeatViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of feats.
    retrieve: API endpoint for returning a particular feat.
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
    filterset_class = FeatFilter

class ConditionFilter(django_filters.FilterSet):

    class Meta:
        model = models.Condition
        fields = {
            'slug': ['in', 'iexact', 'exact', 'in', ],
            'name': ['iexact', 'exact'],
            'desc': ['iexact', 'exact', 'in', 'icontains'],
            'document__slug': ['iexact', 'exact', 'in', ]
        }

class ConditionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of conditions.
    retrieve: API endpoint for returning a particular condition.
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

class RaceFilter(django_filters.FilterSet):

    class Meta:
        model = models.Race
        fields = {
            'slug': ['in', 'iexact', 'exact', 'in', ],
            'name': ['iexact', 'exact'],
            'desc': ['iexact', 'exact', 'in', 'icontains'],
            'document__slug': ['iexact', 'exact', 'in'],
            'asi_desc': ['iexact', 'exact', 'icontains'],
            'age': ['iexact', 'exact', 'icontains'],
            'alignment': ['iexact', 'exact', 'icontains'],
            'size': ['iexact', 'exact', 'icontains'],
            'speed_desc':['iexact', 'exact', 'icontains'],
            'languages': ['iexact', 'exact', 'icontains'],
            'vision': ['iexact', 'exact', 'icontains'],
            'traits': ['iexact', 'exact', 'icontains']
        }

class RaceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of races.
    retrieve: API endpoint for returning a particular race.
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
    filterset_class = RaceFilter

class SubraceFilter(django_filters.FilterSet):
    # Unused, but could be implemented later.
    class Meta:
        model = models.Subrace
        fields = {
            'slug': ['in', 'iexact', 'exact', 'in', ],
            'name': ['iexact', 'exact'],
            'desc': ['iexact', 'exact', 'in', 'icontains'],
            'document__slug': ['iexact', 'exact', 'in', ]
        }

class SubraceViewSet(viewsets.ReadOnlyModelViewSet):
    # Unused, but could be implemented later.
    """
    list: API endpoint that allows viewing of Subraces.
    retrieve: API endpoint for returning a particular subrace.
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

class CharClassFilter(django_filters.FilterSet):

    class Meta:
        model = models.CharClass
        fields = {
            'slug': ['in', 'iexact', 'exact', 'in', ],
            'name': ['iexact', 'exact'],
            'desc': ['iexact', 'exact', 'in', 'icontains'],
            'hit_dice': ['iexact', 'exact', 'in'],
            'hp_at_1st_level': ['iexact', 'exact', 'icontains'],
            'hp_at_higher_levels': ['iexact', 'exact', 'icontains'],
            'prof_armor': ['iexact', 'exact', 'icontains'],
            'prof_weapons': ['iexact', 'exact', 'icontains'],
            'prof_tools': ['iexact', 'exact', 'icontains'],
            'prof_skills': ['iexact', 'exact', 'icontains'],
            'equipment': ['iexact', 'exact', 'icontains'],
            'spellcasting_ability': ['iexact', 'exact', 'icontains'],
            'subtypes_name': ['iexact', 'exact', 'icontains'],
            'document__slug': ['iexact', 'exact', 'in', ]
        }

class CharClassViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of classes and archetypes.
    retrieve: API endpoint for returning a particular class or archetype.
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
    filterset_class = CharClassFilter

class ArchetypeFilter(django_filters.FilterSet):
    # Unused but could be implemented later.
    class Meta:
        model = models.Archetype
        fields = {
            'slug': ['in', 'iexact', 'exact', 'in', ],
            'name': ['iexact', 'exact'],
            'desc': ['iexact', 'exact', 'in', 'icontains'],
            'document__slug': ['iexact', 'exact', 'in', ]
        }

class ArchetypeViewSet(viewsets.ReadOnlyModelViewSet):
    # Unused but could be implemented later.
    """
    list: API endpoint that allows viewing of Archetypes.
    retrieve: API endpoint for returning a particular archetype.
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

class MagicItemFilter(django_filters.FilterSet):

    class Meta:
        model = models.MagicItem
        fields = {
            'slug': ['in', 'iexact', 'exact', 'in', ],
            'name': ['iexact', 'exact'],
            'desc': ['iexact', 'exact', 'in', 'icontains'],
            'type': ['iexact', 'exact', 'icontains'],
            'rarity': ['iexact', 'exact', 'icontains'],
            'requires_attunement': ['iexact', 'exact'],
            'document__slug': ['iexact', 'exact', 'in', ]
        }

class MagicItemViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of magic items.
    retrieve: API endpoint for returning a particular magic item.
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
    filterset_class = MagicItemFilter
    search_fields = ['name']

class WeaponFilter(django_filters.FilterSet):

    class Meta:
        model = models.Weapon
        fields = {
            'slug': ['in', 'iexact', 'exact', 'in', ],
            'name': ['iexact', 'exact'],
            'desc': ['iexact', 'exact', 'in', 'icontains'],
            'cost': ['iexact', 'exact', 'icontains'],
            'damage_dice': ['iexact', 'exact', 'icontains'],
            'damage_type': ['iexact', 'exact', 'icontains'],
            'weight': ['iexact', 'exact', 'icontains'],
            'document__slug': ['iexact', 'exact', 'in', ]
        }

class WeaponViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of weapons.
    retrieve: API endpoint for returning a particular weapon.
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
    filterset_class = WeaponFilter
    search_fields = ['name']

class ArmorFilter(django_filters.FilterSet):

    class Meta:
        model = models.Armor
        fields = {
            'slug': ['in', 'iexact', 'exact', 'in', ],
            'name': ['iexact', 'exact'],
            'desc': ['iexact', 'exact', 'in', 'icontains'],
            'cost': ['iexact', 'exact', 'icontains'],
            'weight': ['iexact', 'exact', 'icontains'],
            'document__slug': ['iexact', 'exact', 'in', ]
        }

class ArmorViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of armor.
    retrieve: API endpoint for returning a particular armor.
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
    filterset_class = ArmorFilter
    search_fields = ['name']
