"""
The model for a spell.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


from .abstracts import HasName, HasDescription
from .document import FromDocument


from .enums import SPELL_TARGET_TYPE_CHOICES, SPELL_TARGET_RANGE_CHOICES, SPELL_EFFECT_SHAPE_CHOICES, SPELL_CASTING_TIME_CHOICES, SPELL_SCHOOL_CHOICES

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

    # Casting target requirements of the spell instance
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

    @property
    def components(self):
        return ["v","s","m"]

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
        help_text="The damage roll for the field in dice notaion. Empty string if no roll.")

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

    @property
    def slot_expended(self):
        if self.level==0:
            return False
        else:
            return True

    @property
    def casting_options(self):
        casting_options=[]
        # Consider adding an empty default?
        if self.ritual:
            casting_options.append(
                {"ritual":{"casting_time":"10 minutes and {}".format(self.get_casting_time_display()),
                "slot_expended":False}})
        if self.level==0 and self.higher_level!="":
            for player_level in range(1,21):
                casting_options.append(
                    {"player_level_{}".format(player_level):{
                        "damage_roll":self.get_damage_at_level(player_level)
                    }}
                )

        if self.level>0 and self.higher_level!="":
            for slot_level in range(self.level+1,11):
                casting_options.append(
                    {"slot_level_{}".format(slot_level):{}}
                )

        return casting_options
    
    def get_damage_at_level(self, level):
        damage_at_level = []
        cantrip_prefix="This spell's damage increases by"
        spell_prefix="When you cast this spell using a spell slot of"
        spell_prefix2="If you cast this spell using a spell slot of"

        if self.higher_level.startswith(cantrip_prefix):
            if level < 5:
                return self.damage_roll
            if level >= 5 and level < 11 :
                for phrase in self.higher_level.split(','):
                    if phrase.find("5th level")>0:
                        damage_roll_5 = phrase.split("5th level")[1].strip().split("(")[1].split(")")[0]
                        return damage_roll_5
            if level >=11 and level < 17:
                for phrase in self.higher_level.split(','): 
                    if phrase.find("11th level")>0:
                        damage_roll_11 = phrase.split("11th level")[1].strip().split("(")[1].split(")")[0]
                        return damage_roll_11
            if level >=17:
                for phrase in self.higher_level.split(','):
                    if phrase.find("17th level")>0:
                        damage_roll_17 = phrase.split("17th level")[1].strip().split("(")[1].split(")")[0]
                        return damage_roll_17
            
            '''for player_level in range(1,21):
                if player_level <5:
                    damage_at_level.append((player_level,self.damage_roll))
                if player_level <11 and player_level>=5 :
                    damage_at_level.append((player_level,self.damage_roll_5))
                if player_level <17 and player_level>=11:
                    damage_at_level.append((player_level,self.damage_roll_11))
                if player_level <21 and player_level>=17:
                    damage_at_level.append((player_level,self.damage_roll_17))
            return damage_at_level[level]'''

        if self.higher_level.startswith(spell_prefix) or self.higher_level.startswith(spell_prefix2):
            pass

