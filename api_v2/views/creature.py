from rest_framework import viewsets

from django_filters import FilterSet

from api_v2 import models
from api_v2 import serializers

from .mixins import EagerLoadingMixin

class CreatureFilterSet(FilterSet):
    '''This is the filterset class for creatures.'''

    class Meta:
        model = models.Creature
        fields = {
            'key': ['in', 'iexact', 'exact' ],
            'name': ['iexact', 'exact', 'icontains'],
            'document__key': ['in','iexact','exact'],
            'document__gamesystem__key': ['in','iexact','exact'],
            'size': ['exact'],
            'category': ['exact', 'iexact'],
            'subcategory': ['exact', 'iexact'],
            'type': ['exact'],
            'challenge_rating_decimal': ['exact','lt','lte','gt','gte'],
            'armor_class': ['exact','lt','lte','gt','gte'],
            'ability_score_strength': ['exact','lt','lte','gt','gte'],
            'ability_score_dexterity': ['exact','lt','lte','gt','gte'],
            'ability_score_constitution': ['exact','lt','lte','gt','gte'],
            'ability_score_intelligence': ['exact','lt','lte','gt','gte'],
            'ability_score_wisdom': ['exact','lt','lte','gt','gte'],
            'ability_score_charisma': ['exact','lt','lte','gt','gte'],
            'saving_throw_strength': ['isnull'],
            'saving_throw_dexterity': ['isnull'],
            'saving_throw_constitution': ['isnull'],
            'saving_throw_intelligence': ['isnull'],
            'saving_throw_wisdom': ['isnull'],
            'saving_throw_charisma': ['isnull'],
            'skill_bonus_acrobatics': ['isnull'],
            'skill_bonus_animal_handling': ['isnull'],
            'skill_bonus_arcana': ['isnull'],
            'skill_bonus_athletics': ['isnull'],
            'skill_bonus_deception': ['isnull'],
            'skill_bonus_history': ['isnull'],
            'skill_bonus_insight': ['isnull'],
            'skill_bonus_intimidation': ['isnull'],
            'skill_bonus_investigation': ['isnull'],
            'skill_bonus_medicine': ['isnull'],
            'skill_bonus_nature': ['isnull'],
            'skill_bonus_perception': ['isnull'],
            'skill_bonus_performance': ['isnull'],
            'skill_bonus_persuasion': ['isnull'],
            'skill_bonus_religion': ['isnull'],
            'skill_bonus_sleight_of_hand': ['isnull'],
            'skill_bonus_stealth': ['isnull'],
            'skill_bonus_survival': ['isnull'],
            'passive_perception': ['exact','lt','lte','gt','gte'],
        }


class CreatureViewSet(EagerLoadingMixin, viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of creatures.
    retrieve: API endpoint for returning a particular creature.
    """
    queryset = models.Creature.objects.all().order_by('pk')
    serializer_class = serializers.CreatureSerializer
    filterset_class = CreatureFilterSet

    select_related_fields = []
    
    prefetch_related_fields = [
        'actions',
        'actions__attacks',
        'creaturesets',
        'condition_immunities',
        'condition_immunities__icon',
        'condition_immunities__document',
        'damage_immunities',
        'damage_resistances',
        'damage_vulnerabilities',
        'document',
        'document__publisher',
        'document__gamesystem',
        'environments',
        'languages',
        'type',
        'size',
        'size__document',
        'traits',
    ]

    def get_serializer(self, *args, **kwargs):
        # Ignore `depth` query parameter on this endpoint. It interacts badly
        # with our custom serializers and is no longer necessary on this view
        if 'depth' in self.request.query_params:
            self.request.query_params._mutable = True
            self.request.query_params.pop('depth', None)
            self.request.query_params._mutable = False
        return super().get_serializer(*args, **kwargs)

class CreatureTypeFilterSet(FilterSet):
    class Meta:
        model = models.CreatureType
        fields = {
            'key': ['in', 'iexact', 'exact' ],
            'name': ['iexact', 'exact','contains'],
            'document__key': ['in','iexact','exact'],
            'document__gamesystem__key': ['in','iexact','exact'],
        }


class CreatureTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of creatures types.
    retrieve: API endpoint for returning a particular creature type.
    """
    queryset = models.CreatureType.objects.all().order_by('pk')
    serializer_class = serializers.CreatureTypeSerializer
    filterset_class = CreatureTypeFilterSet


class CreatureSetFilterSet(FilterSet):
    class Meta:
        model = models.CreatureSet
        fields = {
            'key': ['in', 'iexact', 'exact' ],
            'name': ['iexact', 'exact','contains'],
            'document__key': ['in','iexact','exact'],
            'document__gamesystem__key': ['in','iexact','exact'],
        }


class CreatureSetViewSet(EagerLoadingMixin, viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of creature sets, which is similar to tags.
    retrieve: API endpoint for returning a particular creature set.
    """
    queryset = models.CreatureSet.objects.all().order_by('pk')
    serializer_class = serializers.CreatureSetSerializer
    filterset_class = CreatureSetFilterSet

    prefetch_related_fields = [
        'creatures__actions',
        'creatures__condition_immunities',
        'creatures__damage_resistances',
        'creatures__damage_immunities',
        'creatures__damage_vulnerabilities',
        'creatures__creaturesets',
        'creatures__document',
        'creatures__environments',
        'creatures__size',
        'creatures__traits',
        'creatures__type',
        'creatures__languages',
    ]

class CreatureTraitViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.CreatureTrait.objects.all().order_by('pk')
    serializer_class = serializers.CreatureTraitSerializer