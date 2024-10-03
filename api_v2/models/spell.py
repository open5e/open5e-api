"""
The model for a spell, and supporting objects.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


from .abstracts import HasName, HasDescription
from .abstracts import distance_field, distance_unit_field
from .document import FromDocument
from .characterclass import CharacterClass


from .enums import SPELL_TARGET_TYPE_CHOICES
from .enums import SPELL_TARGET_RANGE_CHOICES, SPELL_CASTING_TIME_CHOICES
from .enums import SPELL_EFFECT_SHAPE_CHOICES, SPELL_EFFECT_DURATIONS
from .enums import CASTING_OPTION_TYPES

class SpellSchool(HasName, HasDescription, FromDocument):
    """The model for a spell school object."""


class Spell(HasName, HasDescription, FromDocument):
    """The model for a spell object."""

   # Casting options and requirements of a spell instance
    level = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(9)],
        help_text='Integer representing the default slot level required by the spell.')

    school = models.ForeignKey(
        "SpellSchool",
        on_delete=models.CASCADE,
        help_text="Spell school, such as 'evocation'")

    higher_level = models.TextField(
        blank=True,
        help_text = "Description of casting the spell at a different level.")

    # Casting target requirements of the spell instance SHOULD BE A LIST
    target_type = models.TextField(
        choices = SPELL_TARGET_TYPE_CHOICES,
        help_text='Spell target type key.')

    range_text = models.TextField( # SWAP TO DISTANCE FIELD
        choices = SPELL_TARGET_RANGE_CHOICES,
        help_text='Spell target range.')

    range = distance_field()
    range_unit = distance_unit_field()

    ritual = models.BooleanField(
        help_text='Whether or not the spell can be cast as a ritual.',
        default=False)

    casting_time = models.TextField(
        choices = SPELL_CASTING_TIME_CHOICES,
        help_text = "Casting time key, such as 'action'")
    
    reaction_condition = models.TextField(
        blank=True,
        null=True,
        help_text='The conditions describing when a reaction spell can be cast')

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
        help_text ='Description of the material specified for the spell.')

    material_cost = models.DecimalField(
        null=True,  # Allow an unspecified cost.
        blank=True,
        default=None,
        max_digits=10,
        decimal_places=2,  # Only track down to 2 decimal places.
        validators=[MinValueValidator(0)],
        help_text='Number representing the cost of the materials of the spell.')

    material_consumed = models.BooleanField(
        help_text='Whether or the material component is consumed during the casting.',
        default=False)

    target_count = models.IntegerField(
        null=True,  # Allow an unspecified count of targets.
        validators=[MinValueValidator(0)],
        help_text='Integer representing the count of targets.')

    saving_throw_ability = models.TextField(
        blank=True,
        help_text = 'Given the spell requires a saving throw, which ability is targeted. Empty string if no saving throw.')

    attack_roll = models.BooleanField(
        default=False,
        help_text='Whether or not the spell effect requires an attack roll.')

    damage_roll = models.TextField(
        blank=True,
        help_text="The damage roll for the field in dice notation. Empty string if no roll.")

    damage_types = models.JSONField(
        default=list,
        blank=True,
        help_text="The types of damage done by the spell in a list.")

    duration = models.TextField(
        choices = SPELL_EFFECT_DURATIONS,
        help_text='Description of the duration of the effect such as "instantaneous" or "1 minute"')

    shape_type = models.TextField(
        null=True,
        blank=True,
        choices = SPELL_EFFECT_SHAPE_CHOICES,
        help_text = 'The shape of the area of effect.')

    shape_size = distance_field()
    shape_size_unit = distance_unit_field()

    concentration = models.BooleanField(
        help_text='Whether the effect requires concentration to be maintained.',
        default=False)

    classes = models.ManyToManyField(CharacterClass)

    def casting_options(self):
        """Options for casting the spell."""
        return self.spellcastingoption_set
    
    def get_shape_size_unit(self):
        if self.shape_size_unit is None:
            return self.document.distance_unit
        return self.shape_size_unit

    def get_range_unit(self):
        if self.range_unit is None:
            return self.document.distance_unit
        return self.range_unit

    def search_result_extra_fields(self):
        return {
            "school": self.school.name,
            "level": self.level,
        }
        
class SpellCastingOption(models.Model):
    """An object representing an alternative way to cast a spell."""

    parent = models.ForeignKey("Spell",on_delete=models.CASCADE)

    type = models.TextField(
        choices=CASTING_OPTION_TYPES,
        help_text="")

    damage_roll = models.TextField(
        null=True,
        blank=True,
        help_text="The damage roll for the field in dice notation. Empty string if no roll.")

    target_count = models.IntegerField(
        null=True,  # Null values mean this value is unchanged from the default casting option.
        validators=[MinValueValidator(0)],
        help_text='Integer representing the count of targets.')

    duration = models.TextField(
        null=True, # Null values mean this value is unchanged from the default casting option.
        help_text='Description of the duration of the effect such as "instantaneous" or "Up to 1 minute"')

    range = models.TextField(
        null=True, # Null values mean this value is unchanged from the default casting option.
        help_text='Description of the range of the spell.')
