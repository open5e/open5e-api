"""The model for an item."""

from django.db import models
from api.models import GameContent
from .weapontype import WeaponType
from .armortype import ArmorType


class Item(Object):
    """
    This is the model for an Item, which is an object that can be used.

    This extends the object model, but adds cost, and is_magical.
    """

    cost = models.DecimalField(
        null=True,  # Allow an unspecified cost.
        max_digits=10,
        decimal_places=2,  # Only track down to 2 decimal places.
        validators=[MinValueValidator(0)],
        help_text='Number representing the cost of the object.')

    is_magical = models.BooleanField(
        null=False,
        default=False,  # An item is not magical unless specified.
        help_text='If the item is a magical item.')

    weapon_type = models.ForeignKey(
        WeaponType,
        null=True)

    armor_type = models.ForeignKey(
        ArmorType,
        null=True)

    def is_weapon(self):
        return self.weapon_type is not None

    def is_armor(self):
        return self.armor_type is not None