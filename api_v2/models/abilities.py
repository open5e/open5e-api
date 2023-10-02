"""
The model for abilities.

Includes ability scores and modifiers, saving throws, skill bonuses, and
passive perception.
"""

from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

from math import floor

# Field value limits
ABILITY_SCORE_MAXIMUM = 30
SAVING_THROW_MINIMUM = -5
SAVING_THROW_MAXIMUM = +20
SKILL_BONUS_MINIMUM = -5
SKILL_BONUS_MAXIMUM = +20
PASSIVE_SCORE_MAXIMUM = 30

# Define a field representing an ability score
def ability_score_field(help_text):
    return models.SmallIntegerField(
        default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(ABILITY_SCORE_MAXIMUM)],
        help_text=help_text)

# Calculate the modifier corresponding to a given ability score
def ability_modifier(score):
  return floor(0.5 * (score - 10))

# Define a field representing a saving throw
def saving_throw_field(help_text):
    return models.SmallIntegerField(
        null=True,
        validators=[
            MinValueValidator(SAVING_THROW_MINIMUM),
            MaxValueValidator(SAVING_THROW_MAXIMUM)],
        help_text=help_text)

# Define a field representing a skill bonus
def skill_bonus_field(help_text):
    return models.SmallIntegerField(
        null=True,
        validators=[
            MinValueValidator(SKILL_BONUS_MINIMUM),
            MaxValueValidator(SKILL_BONUS_MAXIMUM)],
        help_text=help_text)

# Define a field representing a passive score
def passive_score_field(help_text):
    return models.SmallIntegerField(
        default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(PASSIVE_SCORE_MAXIMUM)],
        help_text=help_text)


class Abilities(models.Model):
    """
    This is the definition of the Abilities abstract base class.

    The Abilities class defines the standard six ability scores plus related
    features and will be inherited by Creature.
    """


    # Ability scores

    ability_score_strength = ability_score_field(
        'Integer representing the strength ability.')

    ability_score_dexterity = ability_score_field(
        'Integer representing the dexterity ability.')

    ability_score_constitution = ability_score_field(
        'Integer representing the constitution ability.')

    ability_score_intelligence = ability_score_field(
        'Integer representing the intelligence ability.')

    ability_score_wisdom = ability_score_field(
        'Integer representing the wisdom ability.')

    ability_score_charisma = ability_score_field(
        'Integer representing the charisma ability.')

    def get_ability_scores(self):
        return {
            'strength': self.ability_score_strength,
            'dexterity': self.ability_score_dexterity,
            'constitution': self.ability_score_constitution,
            'intelligence': self.ability_score_intelligence,
            'wisdom': self.ability_score_wisdom,
            'charisma': self.ability_score_charisma,
        }


    # Ability modifiers

    @property
    def modifier_strength(self):
        return ability_modifier(self.ability_score_strength)

    @property
    def modifier_dexterity(self):
        return ability_modifier(self.ability_score_dexterity)

    @property
    def modifier_constitution(self):
        return ability_modifier(self.ability_score_constitution)

    @property
    def modifier_intelligence(self):
        return ability_modifier(self.ability_score_intelligence)

    @property
    def modifier_wisdom(self):
        return ability_modifier(self.ability_score_wisdom)

    @property
    def modifier_charisma(self):
        return ability_modifier(self.ability_score_charisma)

    def get_modifiers(self):
        return {
            'strength': self.modifier_strength,
            'dexterity': self.modifier_dexterity,
            'constitution': self.modifier_constitution,
            'intelligence': self.modifier_intelligence,
            'wisdom': self.modifier_wisdom,
            'charisma': self.modifier_charisma,
        }


    # Saving throws

    # These fields may be null, indicating the default value should be used.

    saving_throw_strength = saving_throw_field(
        'Signed integer added to strength saving throws.')

    saving_throw_dexterity = saving_throw_field(
        'Signed integer added to dexterity saving throws.')

    saving_throw_constitution = saving_throw_field(
        'Signed integer added to constitution saving throws.')

    saving_throw_intelligence = saving_throw_field(
        'Signed integer added to intelligence saving throws.')

    saving_throw_wisdom = saving_throw_field(
        'Signed integer added to wisdom saving throws.')

    saving_throw_charisma = saving_throw_field(
        'Signed integer added to charisma saving throws.')

    def get_saving_throws(self):
        return {
            'strength': self.saving_throw_strength,
            'dexterity': self.saving_throw_dexterity,
            'constitution': self.saving_throw_constitution,
            'intelligence': self.saving_throw_intelligence,
            'wisdom': self.saving_throw_wisdom,
            'charisma': self.saving_throw_charisma,
        }


    # Skill bonuses

    # These fields may be null, indicating the default value should be used.

    skill_bonus_acrobatics = skill_bonus_field(
        'Signed integer added to acrobatics skill checks.')

    skill_bonus_animal_handling = skill_bonus_field(
        'Signed integer added to animal handling skill checks.')

    skill_bonus_arcana = skill_bonus_field(
        'Signed integer added to arcana skill checks.')

    skill_bonus_athletics = skill_bonus_field(
        'Signed integer added to athletics skill checks.')

    skill_bonus_deception = skill_bonus_field(
        'Signed integer added to deception skill checks.')

    skill_bonus_history = skill_bonus_field(
        'Signed integer added to history skill checks.')

    skill_bonus_insight = skill_bonus_field(
        'Signed integer added to insight skill checks.')

    skill_bonus_intimidation = skill_bonus_field(
        'Signed integer added to intimidation skill checks.')

    skill_bonus_investigation = skill_bonus_field(
        'Signed integer added to investigation skill checks.')

    skill_bonus_medicine = skill_bonus_field(
        'Signed integer added to medicine skill checks.')

    skill_bonus_nature = skill_bonus_field(
        'Signed integer added to nature skill checks.')

    skill_bonus_perception = skill_bonus_field(
        'Signed integer added to perception skill checks.')

    skill_bonus_performance = skill_bonus_field(
        'Signed integer added to performance skill checks.')

    skill_bonus_persuasion = skill_bonus_field(
        'Signed integer added to persuasion skill checks.')

    skill_bonus_religion = skill_bonus_field(
        'Signed integer added to religion skill checks.')

    skill_bonus_sleight_of_hand = skill_bonus_field(
        'Signed integer added to sleight of hand skill checks.')

    skill_bonus_stealth = skill_bonus_field(
        'Signed integer added to stealth skill checks.')

    skill_bonus_survival = skill_bonus_field(
        'Signed integer added to survival skill checks.')

    def get_skill_bonuses(self):
        return {
            'acrobatics': self.skill_bonus_acrobatics,
            'animal_handling': self.skill_bonus_animal_handling,
            'arcana': self.skill_bonus_arcana,
            'athletics': self.skill_bonus_athletics,
            'deception': self.skill_bonus_deception,
            'history': self.skill_bonus_history,
            'insight': self.skill_bonus_insight,
            'intimidation': self.skill_bonus_intimidation,
            'investigation': self.skill_bonus_investigation,
            'medicine': self.skill_bonus_medicine,
            'nature': self.skill_bonus_nature,
            'perception': self.skill_bonus_perception,
            'performance': self.skill_bonus_performance,
            'persuasion': self.skill_bonus_persuasion,
            'religion': self.skill_bonus_religion,
            'sleight_of_hand': self.skill_bonus_sleight_of_hand,
            'stealth': self.skill_bonus_stealth,
            'survival': self.skill_bonus_survival,
        }


    # Passive scores

    passive_perception = passive_score_field(
        'Integer representing the passive perception ability.')

    class Meta:
        abstract = True
