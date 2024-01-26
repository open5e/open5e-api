"""
The model for a spell.
"""

from django.db import models
from django.core.validators import MinValueValidator
from django.core.validators import MaxValueValidator

from .abstracts import HasName, HasDescription, FromDocument

from .enum import TARGET_TYPE_CHOICES, TARGET_RANGE_CHOICES, EFFECT_SHAPE_CHOICES

class Spell(HasName, HasDescription, FromDocument):

    # Casting options and requirements of a spell instance
    level = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(9)],
        help_text='Integer representing the minimum slot level required by the spell. Cantrip is 0.')

    # Casting target requirements of the spell instance
    target = models.TextField(
        help_text='Choices for spell targets.')
    
    range = models.TextField(
        choices = TARGET_RANGE_CHOICES,
        help_text='Choices for spell targets.')
    

class SpellCasting(models.Model):
    ritual = models.BooleanField(
        help_text='Whether or not the spell can be cast as a ritual.',
        default=False)

    verbal = models.BooleanField(
        help_text='Whether or not casting the spell requires a verbal component.',
        default=False)

    somatic = models.BooleanField(
        help_text='Whether or not casting the spell requires a verbal component.',
        default=False)

    material = models.BooleanField(
        help_text='Whether or not casting the spell requires a verbal component.',
        default=False)

    material_specified = models.TextField(
        help_text ='A short description of the material required for the spell.')

    material_cost = models.TextField(
        help_text ='The cost of the material.')

    material_consumed = models.BooleanField(
        help_text='Whether or the material component is consumed during the casting.',
        default=False)

    @property
    def components(self):
        return ["v","s","m"]


class SpellEffect(models.Model):
    saving_throw_ability = models.TextField(
        #
    )
    attack_roll = models.BooleanField(
        help_text='Whether or not the spell effect requires an attack roll.',
        default=False)

    damage_roll = models.TextField()

    duration = models.TextField(
        help_text='Description of the duration of the effect such as "instantaneous" or "Up to 1 minute"')
    
    shape_type = models.TextField(
        choices = EFFECT_SHAPE_CHOICES,
        help_text = 'The shape of the area of effect.'
    )
    shape_magnitude = models.IntegerField(
        validators[MinValueValidator(0)],
        help_text = 'The magnitude of the shape (without units).'
    )
    @property
    def shape_size(self):
        return "{}-foot".format(self.shape_magnitude)

    concentration = models.BooleanField(
        help_text='Whether the effect requires concentration to be maintained.',
        default=False)


class SpellSet(HasName, FromDocument):
    spells = models.ManyToManyField(Spell,
                                    help_text="The set of spells.")

