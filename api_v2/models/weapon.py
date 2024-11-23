"""The model for a type of weapon."""

from django.db import models
from django.core.validators import MinValueValidator

from .abstracts import HasName
from .abstracts import distance_field, distance_unit_field
from .document import FromDocument
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers

class Weapon(HasName, FromDocument):
    """
    This model represents types of weapons.

    This does not represent a weapon itself, because that would be an item.
    Only the unique attributes of a weapon are here. An item that is a weapon
    would link to this model instance.
    """

    damage_type = models.ForeignKey(
        "DamageType",
        null=True,
        related_name="+", # No backwards relation.
        on_delete=models.CASCADE,
        help_text='What kind of damage this weapon deals')

    damage_dice = models.CharField(
        null=False,
        max_length=100,
        help_text='The damage dice when used making an attack.')

    versatile_dice = models.CharField(
        null=False,
        default=0,
        max_length=100,
        help_text="""The damage dice when attacking using versatile.
A value of 0 means that the weapon does not have the versatile property.""")

    reach = distance_field()

    range = distance_field()

    long_range = distance_field()
    
    distance_unit = distance_unit_field()
    
    @property
    # or none
    @extend_schema_field(OpenApiTypes.STR)
    def get_distance_unit(self):
        if self.distance_unit is None:
            return self.document.distance_unit
        return self.distance_unit


    is_finesse = models.BooleanField(
        null=False,
        default=False,
        help_text='If the weapon is finesse.')

    is_thrown = models.BooleanField(
        null=False,
        default=False,
        help_text='If the weapon is thrown.')

    is_two_handed = models.BooleanField(
        null=False,
        default=False,
        help_text='If the weapon is two-handed.')

    requires_ammunition = models.BooleanField(
        null=False,
        default=False,
        help_text='If the weapon requires ammunition.')

    requires_loading = models.BooleanField(
        null=False,
        default=False,
        help_text='If the weapon requires loading.')

    is_heavy = models.BooleanField(
        null=False,
        default=False,
        help_text='If the weapon is heavy.')

    is_light = models.BooleanField(
        null=False,
        default=False,
        help_text='If the weapon is light.')

    is_lance = models.BooleanField(
        null=False,
        default=False,
        help_text='If the weapon is a lance.')

    is_net = models.BooleanField(
        null=False,
        default=False,
        help_text='If the weapon is a net.')

    is_simple = models.BooleanField(
        null=False,
        default=False,
        help_text='If the weapon category is simple.')

    is_improvised = models.BooleanField(
        null=False,
        default=False,
        help_text='If the weapon is improvised.')
    
    @property
    @extend_schema_field(OpenApiTypes.BOOL)
    def is_versatile(self):
        return self.versatile_dice != str(0)

    @property
    @extend_schema_field(OpenApiTypes.BOOL)
    def is_martial(self):
        return not self.is_simple

    @property
    @extend_schema_field(OpenApiTypes.BOOL)
    def is_melee(self):
        # Ammunition weapons can only be used as improvised melee weapons.
        return not self.requires_ammunition

    @property
    @extend_schema_field(OpenApiTypes.BOOL)
    def ranged_attack_possible(self):
        # Only ammunition or throw weapons can make ranged attacks.
        return self.requires_ammunition or self.is_thrown

    @property
    # type is any
    @extend_schema_field(OpenApiTypes.BOOL)
    def range_melee(self):
        return self.reach
    
    @property
    @extend_schema_field(OpenApiTypes.BOOL)
    def is_reach(self):
        # A weapon with a longer reach than the default has the reach property.
        return self.reach > 5 

    @property
    @extend_schema_field(serializers.ChoiceField(choices=['special', 'finesse', 'ammunition', 'light', 'heavy', 'thrown', 'loading', 'two-handed', 'versatile', 'reach'])) 
    def properties(self):
        properties = []
        
        range_desc = "(range {}/{})".format(
            str(self.range),
            str(self.long_range))

        versatile_desc = "({})".format(self.versatile_dice)

        if self.is_net or self.is_lance:
            properties.append("special")
        if self.is_finesse:
            properties.append("finesse")
        if self.requires_ammunition:
            properties.append("ammuntion {}".format(range_desc))
        if self.is_light:
            properties.append("light")
        if self.is_heavy:
            properties.append("heavy")
        if self.is_thrown:
            properties.append("thrown {}".format(range_desc))
        if self.requires_loading:
            properties.append("loading")
        if self.is_two_handed:
            properties.append("two-handed")
        if self.is_versatile:
            properties.append("versatile {}".format(versatile_desc))
        if self.is_reach:
            properties.append("reach")
       
        return properties
