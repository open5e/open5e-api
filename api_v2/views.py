from django_filters import FilterSet
from django_filters import BooleanFilter
from django_filters.rest_framework import DjangoFilterBackend
import django_filters
from rest_framework import viewsets

from api_v2 import models
from api_v2 import serializers
from api.schema_generator import CustomSchema


class ItemFilterSet(FilterSet):
    is_magic_item = BooleanFilter(field_name='rarity', lookup_expr='isnull', exclude=True)

    class Meta:
        model = models.Item
        fields = {
            'key': ['in', 'iexact', 'exact' ],
            'name': ['iexact', 'exact'],
            'desc': ['icontains'],
            'cost': ['exact', 'range', 'gt', 'gte', 'lt', 'lte'],
            'weight': ['exact', 'range', 'gt', 'gte', 'lt', 'lte'],
            'rarity': ['exact', 'in', ],
            'requires_attunement': ['exact'],
            'category': ['in', 'iexact', 'exact'],
            'document__key': ['in','iexact','exact']
        }


class ItemViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of items.

    retrieve: API endpoint for returning a particular item.
    """
    queryset = models.Item.objects.all().order_by('pk')
    serializer_class = serializers.ItemSerializer
    filterset_class = ItemFilterSet


class ItemSetFilterSet(FilterSet):

    class Meta:
        model = models.ItemSet
        fields = {
            'key': ['in', 'iexact', 'exact' ],
            'name': ['iexact', 'exact'],
            'document__key': ['in','iexact','exact']
        }


class ItemSetViewSet(viewsets.ReadOnlyModelViewSet):
    """"
    list: API Endpoint for returning a set of itemsets.

    retrieve: API endpoint for return a particular itemset.
    """
    queryset = models.ItemSet.objects.all().order_by('pk')
    serializer_class = serializers.ItemSetSerializer
    filterset_class = ItemSetFilterSet


class RulesetViewSet(viewsets.ReadOnlyModelViewSet):
    """"
    list: API Endpoint for returning a set of rulesets.

    retrieve: API endpoint for return a particular ruleset.
    """
    queryset = models.Ruleset.objects.all().order_by('pk')
    serializer_class = serializers.RulesetSerializer


class DocumentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of documents.
    retrieve: API endpoint for returning a particular document.
    """
    queryset = models.Document.objects.all().order_by('pk')
    serializer_class = serializers.DocumentSerializer
    filterset_fields = '__all__'


class PublisherViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of publishers.
    retrieve: API endpoint for returning a particular publisher.
    """
    queryset = models.Publisher.objects.all().order_by('pk')
    serializer_class = serializers.PublisherSerializer
    filterset_fields = '__all__'


class LicenseViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of licenses.
    retrieve: API endpoint for returning a particular license.
    """
    queryset = models.License.objects.all().order_by('pk')
    serializer_class = serializers.LicenseSerializer
    filterset_fields = '__all__'


class WeaponFilterSet(FilterSet):

    class Meta:
        model = models.Weapon
        fields = {
            'key': ['in', 'iexact', 'exact' ],
            'name': ['iexact', 'exact'],
            'document__key': ['in','iexact','exact'],
            'damage_type': ['in','iexact','exact'],
            'damage_dice': ['in','iexact','exact'],
            'versatile_dice': ['in','iexact','exact'],
            'range_reach': ['exact','lt','lte','gt','gte'],
            'range_normal': ['exact','lt','lte','gt','gte'],
            'range_long': ['exact','lt','lte','gt','gte'],
            'is_finesse': ['exact'],
            'is_thrown': ['exact'],
            'is_two_handed': ['exact'],
            'requires_ammunition': ['exact'],
            'requires_loading': ['exact'],
            'is_heavy': ['exact'],
            'is_light': ['exact'],
            'is_lance': ['exact'],
            'is_net': ['exact'],
            'is_simple': ['exact'],
            'is_improvised': ['exact']
            }


class WeaponViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of weapons.
    retrieve: API endpoint for returning a particular weapon.
    """
    queryset = models.Weapon.objects.all().order_by('pk')
    serializer_class = serializers.WeaponSerializer
    filterset_class = WeaponFilterSet


class ArmorFilterSet(FilterSet):

    class Meta:
        model = models.Armor
        fields = {
            'key': ['in', 'iexact', 'exact' ],
            'name': ['iexact', 'exact'],
            'document__key': ['in','iexact','exact'],
            'grants_stealth_disadvantage': ['exact'],
            'strength_score_required': ['exact','lt','lte','gt','gte'],
            'ac_base': ['exact','lt','lte','gt','gte'],
            'ac_add_dexmod': ['exact'],
            'ac_cap_dexmod': ['exact'],

        }


class ArmorViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of armor.
    retrieve: API endpoint for returning a particular armor.
    """
    queryset = models.Armor.objects.all().order_by('pk')
    serializer_class = serializers.ArmorSerializer
    filterset_class = ArmorFilterSet


class CreatureFilterSet(FilterSet):

    class Meta:
        model = models.Creature
        fields = {
            'key': ['in', 'iexact', 'exact' ],
            'name': ['iexact', 'exact'],
            'document__key': ['in','iexact','exact'],
            'size': ['exact'],
            'armor_class': ['exact','lt','lte','gt','gte'],
            'ability_score_strength': ['exact','lt','lte','gt','gte'],
            'ability_score_dexterity': ['exact','lt','lte','gt','gte'],
            'ability_score_constitution': ['exact','lt','lte','gt','gte'],
            'ability_score_intelligence': ['exact','lt','lte','gt','gte'],
            'ability_score_wisdom': ['exact','lt','lte','gt','gte'],
            'ability_score_charisma': ['exact','lt','lte','gt','gte'],
            'saving_throw_charisma': ['isnull'],
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


class CreatureViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: API endpoint for returning a list of creatures.
    retrieve: API endpoint for returning a particular creature.
    """
    queryset = models.Creature.objects.all().order_by('pk')
    serializer_class = serializers.CreatureSerializer
    filterset_class = CreatureFilterSet
