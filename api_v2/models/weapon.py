"""The model for a type of weapon."""

from django.db import models
from django.core.validators import MinValueValidator

from .abstracts import HasName, HasDescription
from .abstracts import distance_field, distance_unit_field
from .document import FromDocument
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers

class WeaponProperty(HasName, HasDescription, FromDocument):  
  class Meta:
    verbose_name_plural = "Weapon Properties"
    ordering = ["pk"]
  
  def __str__(self):
    return self.name


class WeaponPropertyAssignment(FromDocument):
  """
  This is an intermediate model that is used to assign WeaponProperties to
  Weapons while bundling in any extra contextual data in the `detail` field
  """
  weapon = models.ForeignKey(
    'Weapon',
    related_name='properties',
    on_delete=models.CASCADE
  )
  property = models.ForeignKey(
    'WeaponProperty',
    related_name='weapons',
    on_delete=models.CASCADE,
  )
  detail = models.CharField(null=True, blank=True, max_length=32)
  
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
    def is_martial(self):
        return not self.is_simple