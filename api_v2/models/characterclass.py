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
    def levels(self):
        """Returns basically the class table."""
        # For each feature, get the set of related featureitem levels
        """"""
        return None

    @property
    def features(self):
        """Returns the set of features that are related to this class."""
        return self.feature_set