"""The model for a feat."""
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

from .abstracts import HasName, HasDescription, Modification
from .document import FromDocument
from .enums import DIE_TYPES

class FeatureItem(models.Model):
    """This is the class for an individual class feature item, a subset of a class
    feature. The name field is unused."""
    # Somewhere in here is where you'd define a field that would eventually display as "Rage Damage +2"
    # Also spell slots...?

    feature = models.ForeignKey('Feature', on_delete=models.CASCADE)
    level = models.IntegerField(validators=[MinValueValidator(0),MaxValueValidator(20)])

    def __str__(self):
        return "{} {} ({})".format(
                                 self.feature.character_class.name,
                                 str(self.level),
                                 self.feature.name)


class Feature(HasName, HasDescription, FromDocument):
    """This class represents an individual class feature, such as Rage, or Extra
    Attack."""

    characterclass = models.ForeignKey('CharacterClass',
        on_delete=models.CASCADE)

    def __str__(self):
        return "{} ({})".format(self.name,self.character_class.name)


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

    @property
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
        return self.feature_set

    def levels(self):
        by_level = {}

        for feature in self.feature_set.all():
            for fl in feature.featureitem_set.all():
                if (str(fl.level)) not in by_level.keys():
                    by_level[str(fl.level)] = {}
                    by_level[str(fl.level)]['features'] = []
                
                by_level[str(fl.level)]['features'].append(fl.feature.key)
                by_level[str(fl.level)]['proficiency-bonus'] = self.proficiency_bonus(player_level=fl.level)
                
        return by_level

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
        
        for feature in self.feature_set.all():
            text+='\n' + feature.as_text()

        return text