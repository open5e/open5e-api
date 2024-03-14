"""The abstract model for an object."""

from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

from .abstracts import HasName
from .size import Size
from .enums import OBJECT_SIZE_CHOICES, OBJECT_ARMOR_CLASS_MAXIMUM, OBJECT_HIT_POINT_MAXIMUM


class Object(HasName):
    """
    This is the definition of the Object abstract base class.

    The Object class will be inherited from by Item, Weapon, Character, etc.
    Basically it describes any sort of matter in the 5e world.
    """

    size = models.ForeignKey(
        "Size",
        on_delete=models.CASCADE)

    weight = models.DecimalField(
        default=0,
        null=False,  # Allow an unspecified weight.
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(0)],
        help_text='Number representing the weight of the object.')

    armor_class = models.IntegerField(
        default=0,
        null=False,  # Allow an unspecified armor_class.
        validators=[
            MinValueValidator(0),
            MaxValueValidator(OBJECT_ARMOR_CLASS_MAXIMUM)],
        help_text='Integer representing the armor class of the object.')

    hit_points = models.IntegerField(
        default=0,
        null=False,  # Allow an unspecified hit point value.
        validators=[
            MinValueValidator(0),
            MaxValueValidator(OBJECT_HIT_POINT_MAXIMUM)],
        help_text='Integer representing the hit points of the object.')

    class Meta:
        abstract = True
        ordering = ['pk']
