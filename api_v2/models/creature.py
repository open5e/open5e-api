"""The model for a creature."""

from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from .abilities import Abilities
from .abstracts import Object, HasDescription, HasName
from .document import FromDocument


MONSTER_TYPES = [
    ("ABERRATION", "Aberration"),
    ("BEAST", "Beast"),
    ("CELESTIAL", "Celestial"),
    ("CONSTRUCT", "Construct"),
    ("DRAGON", "Dragon"),
    ("ELEMENTAL", "Elemental"),
    ("FEY", "Fey"),
    ("FIEND", "Fiend"),
    ("GIANT", "Giant"),
    ("HUMANOID", "Humanoid"),
    ("MONSTROSITY", "Monstrosity"),
    ("OOZE", "Ooze"),
    ("PLANT", "Plant"),
    ("UNDEAD", "Undead"),
]

ATTACK_TYPES = [
    ("SPELL", "Spell"),
    ("WEAPON", "Weapon"),
]

DIE_TYPES = [
    ("D4", "d4"),
    ("D6", "d6"),
    ("D8", "d8"),
    ("D10", "d10"),
    ("D12", "d12"),
    ("D20", "d20"),
]

DAMAGE_TYPES = [
    ("ACID", "Acid"),
    ("BLUDGEONING", "Bludgeoning"),
    ("COLD", "Cold"),
    ("FIRE", "Fire"),
    ("FORCE", "Force"),
    ("LIGHTNING", "Lightning"),
    ("NECROTIC", "Necrotic"),
    ("PIERCING", "Piercing"),
    ("POISON", "Poison"),
    ("PSYCHIC", "Psychic"),
    ("RADIANT", "Radiant"),
    ("SLASHING", "Slashing"),
    ("THUNDER", "Thunder"),
]

USES_TYPES = [
    ("PER_DAY", "X/Day"),
    ("RECHARGE_ON_ROLL", "Recharge X-6"),
    ("RECHARGE_AFTER_REST", "Recharge after a Short or Long rest"),
]

def damage_die_count_field():
    return models.SmallIntegerField(
        null=True,
        validators=[MinValueValidator(0)],
        help_text='The number of dice to roll for damage.'
    )

def damage_die_type_field():
    return models.CharField(
        null=True,
        max_length=20,
        choices=DIE_TYPES,
        help_text='What kind of die to roll for damage.'
    )

def damage_bonus_field():
    return models.SmallIntegerField(
        null=True,
        validators=[MinValueValidator(-5), MaxValueValidator(20)],
        help_text='Damage roll modifier.'
    )

def damage_type_field():
    return models.CharField(
        null=True,
        max_length=20,
        choices=DAMAGE_TYPES,
        help_text='What kind of damage this attack deals.'
    )


class Creature(Object, Abilities, FromDocument):
    """
    This is the model for a Creature, per the 5e ruleset.

    This extends the object and abilities models.
    """

    category = models.CharField(
        max_length=100,
        help_text='What category this creature belongs to.'
    )

    alignment = models.CharField(
        max_length=100,
        help_text='The creature\'s allowed alignments.'
    )


class CreatureAction(HasName, HasDescription, FromDocument):

    creature = models.ForeignKey(
        Creature,
        on_delete=models.CASCADE,
        help_text='The creature to which this action belongs.'
    )

    uses_type = models.CharField(
        null=True,
        max_length=20,
        choices=USES_TYPES,
        help_text='How use of the action is limited, if at all.'
    )

    uses_param = models.SmallIntegerField(
        null=True,
        help_text='The parameter X for if the action is limited.'
    )


class CreatureAttack(HasName, FromDocument):

    creature_action = models.ForeignKey(
        CreatureAction,
        on_delete=models.CASCADE,
        help_text='The creature action to which this attack belongs.'
    )

    attack_type = models.CharField(
        max_length=20,
        choices=ATTACK_TYPES,
        help_text='Whether this is a Weapon or Spell attack.'
    )

    to_hit_mod = models.SmallIntegerField(
        validators=[MinValueValidator(-5), MaxValueValidator(20)],
        help_text='Attack roll modifier.'
    )

    reach_ft = models.SmallIntegerField(
        null=True,
        validators=[MinValueValidator(0)],
        help_text='Reach for melee attacks, in feet.'
    )

    range_ft = models.SmallIntegerField(
        null=True,
        validators=[MinValueValidator(0)],
        help_text='Normal range for ranged attacks, in feet.'
    )

    long_range_ft = models.SmallIntegerField(
        null=True,
        validators=[MinValueValidator(0)],
        help_text='Long range for ranged attacks, in feet.'
    )

    target_creature_only = models.BooleanField(
        help_text='If an attack can target creatures only and not objects.'
    )

    # Base damage fields
    damage_die_count = damage_die_count_field()
    damage_die_type = damage_die_type_field()
    damage_bonus = damage_bonus_field()
    damage_type = damage_type_field()

    # Additional damage fields
    extra_damage_die_count = damage_die_count_field()
    extra_damage_die_type = damage_die_type_field()
    extra_damage_bonus = damage_bonus_field()
    extra_damage_type = damage_type_field()


class CreatureType(HasName, HasDescription, FromDocument):
    """The Type of creature, such as Aberration."""


class CreatureSet(HasName, FromDocument):
    """Set that the creature belongs to."""

    creatures = models.ManyToManyField(Creature, related_name="creaturesets",
                                       help_text="The set of creatures.")