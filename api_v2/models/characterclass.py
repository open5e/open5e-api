"""The model for a feat."""
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from rest_framework import serializers

from .abstracts import HasName, HasDescription, Modification
from .abstracts import key_field
from .abilities import Ability
from .document import FromDocument
from .enums import DIE_TYPES, CASTER_TYPES
from drf_spectacular.utils import extend_schema_field, inline_serializer
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers



class ClassFeatureItem(models.Model):
    """This is the class for an individual class feature item, a subset of a class
    feature."""

    key = key_field()

    # Somewhere in here is where you'd define a field that would eventually display as "Rage Damage +2"
    # Also spell slots...?

    parent = models.ForeignKey('ClassFeature', on_delete=models.CASCADE)
    level = models.IntegerField(validators=[MinValueValidator(0),MaxValueValidator(20)])
    detail = models.CharField(
        null=True,
        max_length = 100
    )
    column_value = models.CharField(
        # The value displayed in a column, or null if no value.
        null=True,
        blank=True,
        max_length=20,
        help_text='The value that should be displayed in the table column (where applicable).'
    )

    def __str__(self):
        return "{} {} ({})".format(
                                 self.parent.parent.name,
                                 str(self.level),
                                 self.parent.name)


class ClassFeature(HasName, HasDescription, FromDocument):
    """This class represents an individual class feature, such as Rage, or Extra
    Attack."""

    parent = models.ForeignKey('CharacterClass',
        on_delete=models.CASCADE)

    def gained_at(self):
        return self.classfeatureitem_set.exclude(column_value__isnull=False)
    
    def table_data(self):
        """Returns an array of tabular data relating to the feature. Each
        array element is a table-row of data. Not needed for most features."""

        return self.classfeatureitem_set.exclude(column_value__isnull=True)

    # Infer the type of this feature based on the `key`
    @property
    def feature_type(self):
        if "proficiency-bonus" in self.key: return "PROFICIENCY_BONUS"
        if "proficiencies" in self.key:     return "PROFICIENCIES"
        if "equipment" in self.key:         return "STARTING_EQUIPMENT"
        if "_slots-" in self.key:           return "SPELL_SLOTS"
        if "_spells-known" in self.key:     return "SPELLS_KNOWN"
        if "_cantrips-known" in self.key:   return "CANTRIPS_KNOWN"
        return "CLASS_FEATURE"              # <- base-case

    def __str__(self):
        return "{} ({})".format(self.name,self.parent.name)


class CharacterClass(HasName, FromDocument):
    """The model for a character class or subclass."""

    subclass_of = models.ForeignKey('self',
                                   default=None,
                                   blank=True,
                                   null=True,
                                   on_delete=models.CASCADE)

    hit_dice = models.CharField(
        max_length=100,
        default=None,
        blank=True,
        null=True,
        choices=DIE_TYPES,
        help_text='Dice notation hit dice option.')

    saving_throws = models.ManyToManyField(Ability,
        related_name="characterclass_saving_throws",
        help_text='Saving throw proficiencies for this class.')

    caster_type = models.CharField(
        max_length=100,
        default=None,
        blank=True,
        null=True,
        choices=CASTER_TYPES,
        help_text='Type of caster. Options are full, half, none.')

    @property
    @extend_schema_field(inline_serializer(
        name="hit_points",
        fields={
            # todo: also none
            "hit_dice": serializers.IntegerField(),
            "hit_dice_name": serializers.StringRelatedField(),
            "hit_points_at_1st_level": serializers.IntegerField(),
            "hit_points_at_higher_levels": serializers.IntegerField()
        }
    ))
    def hit_points(self):
        hit_dice_name = "1{} per {} level".format(self.hit_dice, self.name)
        split_dice = self.hit_dice.lower().split("d")[1]
        hit_points_at_1st_level = "{} + your Constitution modifier".format(split_dice)
        half_plus_one = str(int(split_dice)//2 + 1)
        hit_points_at_higher_levels = "1{} (or {}) + your Constitution modifier per {} level after 1st".format(self.hit_dice, half_plus_one, self.name.lower())

        return {
            "hit_dice":self.hit_dice,
            "hit_dice_name":hit_dice_name,
            "hit_points_at_1st_level":hit_points_at_1st_level,
            "hit_points_at_higher_levels":hit_points_at_higher_levels}


    @property
    def is_subclass(self):
        """Returns whether the object is a subclass."""
        return self.subclass_of is not None

    @property
    def features(self):
        """Returns the set of features that are related to this class."""
        return self.classfeature_set

    @extend_schema_field(serializers.DictField(
        child=inline_serializer(
            name="levels",
            fields={
                "features": serializers.ListSerializer(
                    child=serializers.CharField()
                ),
                "proficiency-bonus": serializers.IntegerField(),
                "level": serializers.IntegerField
            }
        )
    ))


    def get_slots_by_player_level(self,level,caster_type):
        # full is for a full caster, not including cantrips.
        # full=False is for a half caster.
        if level<0: # Invalid player level.
            return None
        if level>20: # Invalid player level.
            return None

        full = [[],
        [0,2,0,0,0,0,0,0,0,0],
        [0,3,0,0,0,0,0,0,0,0],
        [0,4,2,0,0,0,0,0,0,0],
        [0,4,3,0,0,0,0,0,0,0],
        [0,4,3,2,0,0,0,0,0,0],
        [0,4,3,3,0,0,0,0,0,0],
        [0,4,3,3,1,0,0,0,0,0],
        [0,4,3,3,2,0,0,0,0,0],
        [0,4,3,3,3,1,0,0,0,0],
        [0,4,3,3,3,2,0,0,0,0],
        [0,4,3,3,3,2,1,0,0,0],
        [0,4,3,3,3,2,1,0,0,0],
        [0,4,3,3,3,2,1,1,0,0],
        [0,4,3,3,3,2,1,1,0,0],
        [0,4,3,3,3,2,1,1,1,0],
        [0,4,3,3,3,2,1,1,1,0],
        [0,4,3,3,3,2,1,1,1,1],
        [0,4,3,3,3,3,1,1,1,1],
        [0,4,3,3,3,3,2,1,1,1],
        [0,4,3,3,3,3,2,2,1,1]
        ]

        half = [[],
        [0,0,0,0,0,0],
        [0,2,0,0,0,0],
        [0,3,0,0,0,0],
        [0,3,0,0,0,0],
        [0,4,2,0,0,0],
        [0,4,2,0,0,0],
        [0,4,3,0,0,0],
        [0,4,3,0,0,0],
        [0,4,3,2,0,0],
        [0,4,3,2,0,0],
        [0,4,3,3,0,0],
        [0,4,3,3,0,0],
        [0,4,3,3,1,0],
        [0,4,3,3,1,0],
        [0,4,3,3,2,0],
        [0,4,3,3,2,0],
        [0,4,3,3,3,1],
        [0,4,3,3,3,1],
        [0,4,3,3,3,2],
        [0,4,3,3,3,2]
        ]

        if caster_type=='FULL':
            return full[level]
        if caster_type=='HALF':
            return half[level]
        else:
            return []

    def proficiency_bonus(self, player_level):
        # Consider as part of enums
        p = [0,2,2,2,2,3,3,3,3,4,4,4,4,5,5,5,5,6,6,6,6]
        return p[player_level]
    
    def __str__(self):
        if self.is_subclass:
            return "{} [{}]".format(self.subclass_of.name, self.name)
        else:
            return self.name

    def as_text(self):
        text = self.name + '\n'
        
        for feature in self.classfeature_set.all():
            text+='\n' + feature.as_text()

        return text

    def search_result_extra_fields(self):
        return {
            "subclass_of": { 
                "name": self.subclass_of.name,
                "key": self.subclass_of.key
            } if self.subclass_of else None
        }
