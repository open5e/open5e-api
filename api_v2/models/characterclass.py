"""The model for a feat."""
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

from .abstracts import HasName, HasDescription, Modification
from .document import FromDocument

class FeatureItem(Modification):
    """This is the class for an individual class feature item, a subset of a class
    feature. The name field is unused."""

    feature = models.ForeignKey('Feature', on_delete=models.CASCADE)
    level = models.IntegerField(validators=[MinValueValidator(0),MaxValueValidator(20)])

class Feature(HasName, HasDescription, FromDocument):
    """This class represents an individual class feature, such as Rage, or Extra
    Attack."""

    character_class = models.ForeignKey('CharacterClass',
        on_delete=models.CASCADE)

    def levels(self):
        return self.featureitem_set


class CharacterClass(HasName, FromDocument):
    """The model for a character class or subclass."""
    subclass_of = models.ForeignKey('self',
                                   default=None,
                                   blank=True,
                                   null=True,
                                   on_delete=models.CASCADE)
    
    @property
    def is_subclass(self):
        """Returns whether the object is a subclass."""
        return self.subclass_of is not None

    @property
    def features(self):
        """Returns the set of features that are related to this class."""
        return self.feature_set

    def features_by_levels(self):
        by_level = dict.fromkeys(range(1,21),set([]))

        for feature in self.feature_set.all():
            for fl in feature.featureitem_set.all():
                if fl.level == 1:
                    by_level[1].add(feature.key)

        return by_level
