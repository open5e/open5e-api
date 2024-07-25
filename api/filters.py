import django_filters
from api import models


class CommonFilterSet(django_filters.FilterSet):
    document__slug__not_in = django_filters.BaseInFilter(
        field_name="document__slug", exclude=True
    )


class SpellFilter(CommonFilterSet):
    level_int = django_filters.NumberFilter(field_name="spell_level")
    concentration = django_filters.CharFilter(field_name="concentration")
    components = django_filters.CharFilter(field_name="components")
    spell_lists_not = django_filters.CharFilter(field_name="spell_lists", exclude=True)

    class Meta:
        model = models.Spell
        fields = {
            "slug": [
                "in",
                "iexact",
                "exact",
                "in",
            ],
            "name": ["iexact", "exact", "icontains"],
            "spell_level": ["exact", "range", "gt", "gte", "lt", "lte"],
            "target_range_sort": ["exact", "range", "gt", "gte", "lt", "lte"],
            "school": [
                "iexact",
                "exact",
                "in",
            ],
            "duration": [
                "iexact",
                "exact",
                "in",
            ],
            "requires_concentration": ["exact"],
            "requires_verbal_components": ["exact"],
            "requires_somatic_components": ["exact"],
            "requires_material_components": ["exact"],
            "casting_time": [
                "iexact",
                "exact",
                "in",
            ],
            "dnd_class": ["iexact", "exact", "in", "icontains"],
            "spell_lists": ["exact"],
            "document__slug": [
                "iexact",
                "exact",
                "in",
            ],
        }


class SpellListFilter(CommonFilterSet):
    class Meta:
        model = models.SpellList
        fields = {
            "slug": [
                "in",
                "iexact",
                "exact",
                "in",
            ],
            "name": ["iexact", "exact", "icontains"],
            "desc": ["iexact", "exact", "in", "icontains"],
            "document__slug": [
                "iexact",
                "exact",
                "in",
            ],
        }


class MonsterFilter(CommonFilterSet):
    class Meta:
        model = models.Monster
        fields = {
            "slug": [
                "in",
                "iexact",
                "exact",
                "in",
            ],
            "name": ["iexact", "exact", "icontains"],
            "desc": ["iexact", "exact", "in", "icontains"],
            "cr": ["exact", "range", "gt", "gte", "lt", "lte"],
            "hit_points": ["exact", "range", "gt", "gte", "lt", "lte"],
            "armor_class": ["exact", "range", "gt", "gte", "lt", "lte"],
            "type": ["iexact", "exact", "in", "icontains"],
            "size": ["iexact", "exact", "in", "icontains"],
            "page_no": ["exact", "range", "gt", "gte", "lt", "lte"],
            "document__slug": [
                "iexact",
                "exact",
                "in",
            ],
        }


class BackgroundFilter(CommonFilterSet):
    class Meta:
        model = models.Background
        fields = {
            "slug": [
                "in",
                "iexact",
                "exact",
                "in",
            ],
            "name": ["iexact", "exact", "icontains"],
            "skill_proficiencies": ["iexact", "exact", "icontains"],
            "tool_proficiencies": ["iexact", "exact", "icontains"],
            "languages": ["iexact", "exact", "icontains"],
            "feature": ["iexact", "exact", "icontains"],
            "feature_desc": ["iexact", "exact", "icontains"],
            "desc": ["iexact", "exact", "in", "icontains"],
            "document__slug": [
                "iexact",
                "exact",
                "in",
            ],
        }


class PlaneFilter(CommonFilterSet):
    class Meta:
        model = models.Plane
        fields = {
            "slug": [
                "in",
                "iexact",
                "exact",
                "in",
            ],
            "name": ["iexact", "exact", "icontains"],
            "desc": ["iexact", "exact", "in", "icontains"],
            "document__slug": [
                "iexact",
                "exact",
                "in",
            ],
        }


class SectionFilter(CommonFilterSet):
    class Meta:
        model = models.Section
        fields = {
            "slug": [
                "in",
                "iexact",
                "exact",
                "in",
            ],
            "name": ["iexact", "exact", "icontains"],
            "desc": ["iexact", "exact", "in", "icontains"],
            "parent": ["iexact", "exact", "in", "icontains"],
            "document__slug": [
                "iexact",
                "exact",
                "in",
            ],
        }


class FeatFilter(CommonFilterSet):
    class Meta:
        model = models.Feat
        fields = {
            "slug": [
                "in",
                "iexact",
                "exact",
                "in",
            ],
            "name": ["iexact", "exact", "icontains"],
            "desc": ["iexact", "exact", "in", "icontains"],
            "document__slug": ["iexact", "exact", "in"],
        }


class ConditionFilter(CommonFilterSet):
    class Meta:
        model = models.Condition
        fields = {
            "slug": [
                "in",
                "iexact",
                "exact",
                "in",
            ],
            "name": ["iexact", "exact", "icontains"],
            "desc": ["iexact", "exact", "in", "icontains"],
            "document__slug": [
                "iexact",
                "exact",
                "in",
            ],
        }


class RaceFilter(CommonFilterSet):
    class Meta:
        model = models.Race
        fields = {
            "slug": [
                "in",
                "iexact",
                "exact",
                "in",
            ],
            "name": ["iexact", "exact", "icontains"],
            "desc": ["iexact", "exact", "in", "icontains"],
            "document__slug": ["iexact", "exact", "in"],
            "asi_desc": ["iexact", "exact", "icontains"],
            "age": ["iexact", "exact", "icontains"],
            "alignment": ["iexact", "exact", "icontains"],
            "size": ["iexact", "exact", "icontains"],
            "speed_desc": ["iexact", "exact", "icontains"],
            "languages": ["iexact", "exact", "icontains"],
            "vision": ["iexact", "exact", "icontains"],
            "traits": ["iexact", "exact", "icontains"],
        }


class SubraceFilter(CommonFilterSet):
    # Unused, but could be implemented later.
    class Meta:
        model = models.Subrace
        fields = {
            "slug": [
                "in",
                "iexact",
                "exact",
                "in",
            ],
            "name": ["iexact", "exact", "icontains"],
            "desc": ["iexact", "exact", "in", "icontains"],
            "document__slug": [
                "iexact",
                "exact",
                "in",
            ],
        }


class CharClassFilter(CommonFilterSet):
    class Meta:
        model = models.CharClass
        fields = {
            "slug": [
                "in",
                "iexact",
                "exact",
                "in",
            ],
            "name": ["iexact", "exact", "icontains"],
            "desc": ["iexact", "exact", "in", "icontains"],
            "hit_dice": ["iexact", "exact", "in"],
            "hp_at_1st_level": ["iexact", "exact", "icontains"],
            "hp_at_higher_levels": ["iexact", "exact", "icontains"],
            "prof_armor": ["iexact", "exact", "icontains"],
            "prof_weapons": ["iexact", "exact", "icontains"],
            "prof_tools": ["iexact", "exact", "icontains"],
            "prof_skills": ["iexact", "exact", "icontains"],
            "equipment": ["iexact", "exact", "icontains"],
            "spellcasting_ability": ["iexact", "exact", "icontains"],
            "subtypes_name": ["iexact", "exact", "icontains"],
            "document__slug": [
                "iexact",
                "exact",
                "in",
            ],
        }


class ArchetypeFilter(CommonFilterSet):
    # Unused but could be implemented later.
    class Meta:
        model = models.Archetype
        fields = {
            "slug": [
                "in",
                "iexact",
                "exact",
                "in",
            ],
            "name": ["iexact", "exact", "icontains"],
            "desc": ["iexact", "exact", "in", "icontains"],
            "document__slug": [
                "iexact",
                "exact",
                "in",
            ],
        }


class MagicItemFilter(CommonFilterSet):
    class Meta:
        model = models.MagicItem
        fields = {
            "slug": [
                "in",
                "iexact",
                "exact",
                "in",
            ],
            "name": ["iexact", "exact", "icontains"],
            "desc": ["iexact", "exact", "in", "icontains"],
            "type": ["iexact", "exact", "icontains"],
            "rarity": ["iexact", "exact", "icontains"],
            "requires_attunement": ["iexact", "exact"],
            "document__slug": [
                "iexact",
                "exact",
                "in",
            ],
        }


class WeaponFilter(CommonFilterSet):
    class Meta:
        model = models.Weapon
        fields = {
            "slug": [
                "in",
                "iexact",
                "exact",
                "in",
            ],
            "name": ["iexact", "exact", "icontains"],
            "desc": ["iexact", "exact", "in", "icontains"],
            "cost": ["iexact", "exact", "icontains"],
            "damage_dice": ["iexact", "exact", "icontains"],
            "damage_type": ["iexact", "exact", "icontains"],
            "weight": ["iexact", "exact", "icontains"],
            "document__slug": [
                "iexact",
                "exact",
                "in",
            ],
        }


class ArmorFilter(CommonFilterSet):
    class Meta:
        model = models.Armor
        fields = {
            "slug": [
                "in",
                "iexact",
                "exact",
                "in",
            ],
            "name": ["iexact", "exact", "icontains"],
            "desc": ["iexact", "exact", "in", "icontains"],
            "cost": ["iexact", "exact", "icontains"],
            "weight": ["iexact", "exact", "icontains"],
            "document__slug": [
                "iexact",
                "exact",
                "in",
            ],
        }
