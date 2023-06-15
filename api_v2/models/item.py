"""The model for an item."""

from django.db import models
from django.core.validators import MinValueValidator
from django.urls import reverse

from api.models import GameContent
from .weapontype import WeaponType
from .armortype import ArmorType
from .magicitemtype import MagicItemType
from .abstracts import Object


class Item(Object, HasDescription, FromDocument):
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

    weapon_type = models.ForeignKey(
        WeaponType,
        on_delete=models.CASCADE,
        null=True)

    armor_type = models.ForeignKey(
        ArmorType,
        on_delete=models.CASCADE,
        null=True)
    
    magic_item_type = models.ForeignKey(
        MagicItemType,
        on_delete=models.CASCADE,
        null=True)

    @property
    def is_weapon(self):
        return self.weapon_type is not None

    @property
    def is_armor(self):
        return self.armor_type is not None

    @property 
    def is_magic_item(self):
        return self.magic_item_type is not None