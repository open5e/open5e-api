"""
The model for a spell.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


from .abstracts import HasName, HasDescription
from .document import FromDocument


from .enums import *

class Spell(HasName, HasDescription, FromDocument):
    version = 'default'

   # Casting options and requirements of a spell instance
    level = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(9)],
        help_text='Integer representing the minimum slot level required by the spell. Cantrip is 0.')

    school = models.TextField(
        choices = SPELL_SCHOOL_CHOICES,
        help_text = "Spell school, such as 'Evocation'")

    higher_level = models.TextField(
        help_text = "Description of casting the spell at a different level.'")

    # Casting target requirements of the spell instance SHOULD BE A LIST
    target_type = models.TextField(
        choices = SPELL_TARGET_TYPE_CHOICES,
        help_text='Choices for spell targets.')
    
    range = models.TextField(
        choices = SPELL_TARGET_RANGE_CHOICES,
        help_text='Choices for spell targets.')

    ritual = models.BooleanField(
        help_text='Whether or not the spell can be cast as a ritual.',
        default=False)

    casting_time = models.TextField(
        choices = SPELL_CASTING_TIME_CHOICES,
        help_text = "Casting time name, such as '1 action'")

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
        blank=True,
        help_text ='A short description of the material required for the spell.')

    material_cost = models.TextField(
        help_text ='The cost of the material.')

    material_consumed = models.BooleanField(
        help_text='Whether or the material component is consumed during the casting.',
        default=False)

    target_count = models.TextField(
        help_text=''
    )

    saving_throw_ability = models.TextField(
        blank=True,
        help_text = 'Given the spell requires a saving throw, which ability is targeted. Empty string if no saving throw.'
    )
    attack_roll = models.BooleanField(
        default=False,
        help_text='Whether or not the spell effect requires an attack roll.')

    damage_roll = models.TextField(
        blank=True,
        help_text="The damage roll for the field in dice notation. Empty string if no roll.")

    damage_types = models.JSONField(
        default=list,
        help_text="The types of damage done by the spell in a list.")

    duration = models.TextField(
        help_text='Description of the duration of the effect such as "instantaneous" or "Up to 1 minute"')
    
    shape_type = models.TextField(
        null=True,
        choices = SPELL_EFFECT_SHAPE_CHOICES,
        help_text = 'The shape of the area of effect.'
    )
    shape_magnitude = models.IntegerField(
        null=True,
        validators=[MinValueValidator(0)],
        help_text = 'The magnitude of the shape (without units).'
    )
    @property
    def shape_size(self):
        return "{}-foot".format(self.shape_magnitude)

    concentration = models.BooleanField(
        help_text='Whether the effect requires concentration to be maintained.',
        default=False)

    def casting_options(self):
        return self.castingoption_set

class CastingOption(models.Model):
    spell = models.ForeignKey("Spell",on_delete=models.CASCADE)
    
    type = models.TextField(
        choices=CASTING_OPTION_TYPES,
        help_text="")

    damage_roll = models.TextField(
        null=True, # Null values mean this value is unchanged from the default casting option.
        help_text="The damage roll for the field in dice notation. Null if options don't affect damage roll.")

    target_count = models.TextField(
        null=True, # Null values mean this value is unchanged from the default casting option.
        help_text='The count of targets for this casting of the spell.'
    )
    duration = models.TextField(
        null=True, # Null values mean this value is unchanged from the default casting option.
        help_text='Description of the duration of the effect such as "instantaneous" or "Up to 1 minute"')

    range = models.TextField(
        null=True, # Null values mean this value is unchanged from the default casting option.
        help_text='asdf')
