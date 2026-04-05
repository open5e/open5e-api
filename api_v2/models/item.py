"""The model for an item."""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from .weapon import Weapon
from .armor import Armor
from .abstracts import HasName, HasDescription, HasPrice
from .object import Object
from .damagetype import DamageType
from .document import FromDocument
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
import decimal

class ItemRarity(HasName, FromDocument):
    """A class describing the rarity of items."""
    rank = models.IntegerField(
        unique=True,
        help_text='Ranking of the rarity, most common has the lowest values.')


class ItemCategory(HasName, FromDocument):
    """A class describing categories of items."""


class ItemBase(models.Model):
    """
    Common inheritance of Item and MagicItem models
    """
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
        null=False
    )

    damage_vulnerabilities = models.ManyToManyField(DamageType,
        related_name="%(class)s_damage_vulnerabilities")

    damage_immunities = models.ManyToManyField(DamageType,
        related_name="%(class)s_damage_immunities")

    damage_resistances = models.ManyToManyField(DamageType,
        related_name="%(class)s_damage_resistances")
    
    class Meta:
        abstract = True

class Item(ItemBase, Object, HasDescription, FromDocument, HasPrice):
    """
    This is the model for an Item, which is an object that can be used.

    This extends the object model, but adds cost, and is_magical.
    """
    pass


class MagicItem(ItemBase, Object, HasDescription, FromDocument, HasPrice):
    requires_attunement = models.BooleanField(
        null=False,
        default=False,
        help_text='If the item requires attunement.')

    attunement_detail = models.CharField(
        null=True,
        blank=True,
        max_length=128,
    )

    rarity = models.ForeignKey(
        "ItemRarity",
        null=True,
        on_delete=models.CASCADE,
        help_text="Rarity object.")


class ItemSet(HasName, HasDescription, FromDocument):
    """A set of items to be referenced."""

    items = models.ManyToManyField(Item, related_name="itemsets",help_text="The set of items.")
