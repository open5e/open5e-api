"""
The model for an object.
"""

from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.template.defaultfilters import slugify


class HasName(models.Model):
    name = models.TextField(
        help_text='Name of the item.')

    @property 
    def slug(self):
        return slugify(self.name)

    @property
    def abbr(self):
        if ' ' in self.name:
            # Name contains space or spaces.
            words = self.name.split()
            letters = [word[0] for word in words]
            return "".join(letters)
        else:
            return self.slug

    def __str__(self):
        return self.slug

    class Meta:
        abstract = True


class HasDescription(models.Model):
    desc = models.TextField(
        help_text='Description of the game content item. Markdown.')
    class Meta:
        abstract = True


class Object(HasName):
    """
    This is the definition of the Object abstract base class.

    The Object class will be inherited from by Item, Weapon, Character, etc.
    Basically it describes any sort of matter in the 5e world.
    """

    # Enumerating sizes, so they are sortable.
    SIZE_CHOICES = [
        (1, "Tiny"),
        (2, "Small"),
        (3, "Medium"),
        (4, "Large"),
        (5, "Huge"),
        (6, "Gargantuan")]

    # Setting a reasonable maximum for AC.
    ARMOR_CLASS_MAXIMUM = 100

    # Setting a reasonable maximum for HP.
    HIT_POINT_MAXIMUM = 10000

    size = models.IntegerField(
        null=True,  # Allow an unspecified size.
        choices=SIZE_CHOICES,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(6)],
        help_text='Integer representing the size of the object.')

    weight = models.DecimalField(
        null=True,  # Allow an unspecified weight.
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(0)],
        help_text='Number representing the weight of the object.')

    armor_class = models.IntegerField(
        null=True,  # Allow an unspecified armor_class.
        validators=[
            MinValueValidator(0),
            MaxValueValidator(ARMOR_CLASS_MAXIMUM)],
        help_text='Integer representing the armor class of the object.')

    hit_points = models.IntegerField(
        null=True,  # Allow an unspecified hit point value.
        validators=[
            MinValueValidator(0),
            MaxValueValidator(HIT_POINT_MAXIMUM)],
        help_text='Integer representing the hit points of the object.')

    damage_immunities = models.JSONField(
        null=False,  # Force an empty list if unspecified.
        default=list,
        #validators=[damage_type_validator],
        help_text='List of damage types that this is immune to.')

    damage_resistances = models.JSONField(
        null=False,  # Force an empty list if unspecified.
        default=list,
        #validators=[damage_type_validator],
        help_text='List of damage types that this is resistant to.')

    damage_vulnerabilities = models.JSONField(
        null=False,  # Force an empty list if unspecified.
        default=list,
        #validators=[damage_type_validator],
        help_text='List of damage types that this is vulnerable to.')

    class Meta:
        abstract = True