"""The model for an item."""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from .weapon import Weapon
from .armor import Armor
from .abstracts import HasName, HasDescription
from .object import Object
from .damagetype import DamageType
from .document import FromDocument


class ItemRarity(HasName, FromDocument):
    """A class describing the rarity of items."""
    rank = models.IntegerField(
        unique=True,
        help_text='Ranking of the rarity, most common has the lowest values.')


class ItemCategory(HasName, FromDocument):
    """A class describing categories of items."""


class Item(Object, HasDescription, FromDocument):
    """
    This is the model for an Item, which is an object that can be used.

    This extends the object model, but adds cost, and is_magical.
    """

    cost = models.DecimalField(
        null=True,  # Allow an unspecified cost.
        default=None,
        max_digits=10,
        decimal_places=2,  # Only track down to 2 decimal places.
        validators=[MinValueValidator(0)],
        help_text='Number representing the cost of the object.')

    weapon = models.ForeignKey(
        Weapon,
        on_delete=models.CASCADE,
        default=None,
        blank=True,
        null=True)

    armor = models.ForeignKey(
        Armor,
        on_delete=models.CASCADE,
        default=None,
        blank=True,
        null=True)

    category = models.ForeignKey(
        ItemCategory,
        on_delete=models.CASCADE,
        null=False)

    requires_attunement = models.BooleanField(
        null=False,
        default=False,  # An item is not magical unless specified.
        help_text='If the item requires attunement.')

    rarity = models.ForeignKey(
        "ItemRarity",
        null=True,
        on_delete=models.CASCADE,
        help_text="Rarity object.")

    damage_vulnerabilities = models.ManyToManyField(DamageType,
        related_name="item_damage_vulnerabilities")

    damage_immunities = models.ManyToManyField(DamageType,
        related_name="item_damage_immunities")

    damage_resistances = models.ManyToManyField(DamageType,
        related_name="item_damage_resistances")

    @property 
    def is_magic_item(self):
        return self.rarity is not None

    def search_result_extra_fields(self):
        return {
            "is_magic_item": self.is_magic_item,
            "type": self.category.name if self.is_magic_item else None,
            "rarity": self.rarity.name if self.is_magic_item else None,
        }


class ItemSet(HasName, HasDescription, FromDocument):
    """A set of items to be referenced."""

    items = models.ManyToManyField(Item, related_name="itemsets",help_text="The set of items.")
