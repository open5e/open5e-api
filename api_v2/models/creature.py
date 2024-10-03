"""The model for a creature."""
from fractions import Fraction

from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from .abstracts import HasAbilities, HasSenses
from .language import HasLanguage
from .abstracts import HasDescription, HasName, Modification
from .abstracts import damage_die_count_field, damage_die_type_field
from .abstracts import damage_bonus_field, key_field
from .object import Object
from .condition import Condition
from .damagetype import DamageType
from .document import FromDocument
from .speed import HasSpeed
from .enums import CREATURE_ATTACK_TYPES, CREATURE_USES_TYPES, ACTION_TYPES



class CreatureType(HasName, HasDescription, FromDocument):
    """The Type of creature, such as Aberration."""


class Creature(Object, HasAbilities, HasSenses, HasLanguage, HasSpeed, FromDocument):
    """
    This is the model for a Creature, per the 5e ruleset.

    This extends the object and abilities models.
    """

    type = models.ForeignKey(
        CreatureType,
        on_delete=models.CASCADE,
        help_text="Type of creature, such as Aberration."
    )

    category = models.CharField(
        max_length=100,
        help_text='What category this creature belongs to.'
    )

    subcategory = models.CharField(
        max_length=100,
        null=True,
        help_text='What subcategory this creature belongs to.'
    )

    alignment = models.CharField(
        max_length=100,
        help_text='The creature\'s allowed alignments.'
    )

    damage_vulnerabilities = models.ManyToManyField(DamageType,
        related_name="creature_damage_vulnerabilities")

    damage_immunities = models.ManyToManyField(DamageType,
        related_name="creature_damage_immunities")

    damage_resistances = models.ManyToManyField(DamageType,
        related_name="creature_damage_resistances")

    condition_immunities = models.ManyToManyField(
        Condition,
        help_text="Conditions that this creature is immune to."
        )

    challenge_rating_decimal = models.DecimalField(
        null=False,
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(0),MaxValueValidator(30)],
        help_text="Challenge Rating field as a decimal number."
    )

    experience_points_integer = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Optional override for calculated XP based on CR."
    )

    def as_text(self):
        text = self.name + '\n'
        for action in self.creatureaction_set.all():
            text+='\n' + action.as_text()

        return text

    def search_result_extra_fields(self):
        return {
            "cr": self.challenge_rating_text,
            "type": self.type.name,
            "size": self.size.name,   
        }

    @property
    def creatureset(self):
        '''Helper method to rename and return creaturesets.'''
        return self.creaturesets.all()

    @property
    def challenge_rating_text(self):
        '''Challenge rating as text string representation of a fraction or integer. '''
        return str(Fraction(self.challenge_rating_decimal))

    @property
    def experience_points(self):
        if self.experience_points_integer is not None:
            return self.experience_points_integer
        else:
            xp_by_cr_lookup = {
                "0":0,
                "1/8":25,
                "1/4":50,
                "1/2":100,
                "1":200,
                "2":450,
                "3":700,
                "4":1100,
                "5":1800,
                "6":2300,
                "7":2900,
                "8":3900,
                "9":5000,
                "10":5900,
                "11":7200,
                "12":8400,
                "13":10000,
                "14":11500,
                "15":13000,
                "16":15000,
                "17":18000,
                "18":20000,
                "19":22000,
                "20":25000,
                "21":33000,
                "22":41000,
                "23":50000,
                "24":62000,
                "25":75000,
                "26":90000,
                "27":105000,
                "28":120000,
                "29":135000,
                "30":155000,
            }

            try:
                return xp_by_cr_lookup[str(Fraction(self.challenge_rating_decimal))]
            except:
                return None


    @property
    def actions(self):
        """Returns the set of actions that are related to this creature."""
        return self.creatureaction_set


class CreatureAction(HasName, HasDescription):
    """Describes an action available to a creature."""
    key = key_field()

    parent = models.ForeignKey(
        Creature,
        on_delete=models.CASCADE,
        help_text='The creature to which this action belongs.'
    )

    uses_type = models.CharField(
        blank=True,
        null=True,
        max_length=20,
        choices=CREATURE_USES_TYPES,
        help_text='How use of the action is limited, if at all.'
    )

    uses_param = models.SmallIntegerField(
        blank=True,
        null=True,
        help_text='The parameter X for if the action is limited.'
    )

    action_type = models.CharField(
        blank=True,
        null=True,
        max_length=20,
        default="ACTION",
        choices=ACTION_TYPES,
        help_text='The type of action used.'
    )

    form_condition = models.CharField(
        blank=True,
        null=True,
        default=None,
        max_length=100,
        help_text='Description of form-based conditions for this action.'
    )

    legendary_cost = models.SmallIntegerField(
        blank=True,
        null=True,
        default=None,
        help_text='0 if not legendary, else, the number of legendary actions this costs.'
    )


    def as_text(self):
        '''Text representation of creature is name/desc.'''
        text = self.name + '\n' + self.desc

        return text


class CreatureActionAttack(HasName):
    """Describes an attack action used by a creature."""
    key = key_field()

    parent = models.ForeignKey(
        CreatureAction,
        on_delete=models.CASCADE,
        help_text='The creature action to which this attack belongs.'
    )

    attack_type = models.CharField(
        max_length=20,
        choices=CREATURE_ATTACK_TYPES,
        help_text='Whether this is a Weapon or Spell attack.'
    )

    to_hit_mod = models.SmallIntegerField(
        validators=[MinValueValidator(-5), MaxValueValidator(20)],
        help_text='Attack roll modifier.'
    )

    reach_ft = models.SmallIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        help_text='Reach for melee attacks, in feet.'
    )

    range_ft = models.SmallIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        help_text='Normal range for ranged attacks, in feet.'
    )

    long_range_ft = models.SmallIntegerField(
        blank=True,
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

    damage_type = models.ForeignKey(
        "DamageType",
        blank=True,
        null=True,
        related_name="+", # No backwards relation.
        on_delete=models.CASCADE,
        help_text='What kind of damage this attack deals')

    # Additional damage fields
    extra_damage_die_count = damage_die_count_field()
    extra_damage_die_type = damage_die_type_field()
    extra_damage_bonus = damage_bonus_field()

    extra_damage_type = models.ForeignKey(
        "DamageType",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="+", # No backwards relation.
        help_text='What kind of extra damage this attack deals')


class CreatureTrait(Modification):
    """This is the model for a creature special trait.

    It inherits from modification, which is an abstract concept.
    """
    key = key_field()
    parent = models.ForeignKey('Creature', on_delete=models.CASCADE)


class CreatureSet(HasName, FromDocument):
    """Set that the creature belongs to."""

    creatures = models.ManyToManyField(Creature, related_name="creaturesets",
                                       help_text="The set of creatures.")
