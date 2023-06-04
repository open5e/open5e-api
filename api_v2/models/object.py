"""
The model for an object.
"""

from django.db import models
from api.models import GameContent


class Object(GameContent):
    """
    This is the definition of the Object abstract base class.

    The Object class will be inherited from by Item, Weapon, Character, etc.
    Basically it describes any sort of matter in the 5e world.
    """

    SIZE_CHOICES = [
        (0, "Non-existent"),
        (1, "Tiny"),
        (2, "Small"),
        (3, "Medium"),
        (4, "Large"),
        (5, "Huge"),
        (6, "Gargantuan")]

    size = models.IntegerField(
        null=False,
        default=0,
        choices=SIZE_CHOICES,
        validators=[MinValueValidator(0), MaxValueValidator(6)],
        help_text='Integer representing the hit size of the object. 1 is Tiny, 6 is Gargantuan')

    weight = models.DecimalField(
        null=False,
        max_digits=10,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Integer representing the weight of the object.')

    armor_class = models.IntegerField(
        null=False,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Integer representing the armor class of the object.')

    hit_points = models.IntegerField(
        null=False,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(10000)],
        help_text='Integer representing the hit points of the object.')

    damage_immunities = models.JSONField(
        null=False,
        default=[],
        validators=[damage_type_validator],
        help_text='List of damage types that this is immune to.')

    damage_resistances = models.JSONField(
        null=False,
        default=[],
        validators=[damage_type_validator],
        help_text='List of damage types that this is resistant to.')

    damage_vulnerabilities = models.JSONField(
        null=False,
        default=[],
        validators=[damage_type_validator],
        help_text='List of damage types that this is vulnerable to.')

    class Meta:
        abstract = True
