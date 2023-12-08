"""The model for a feat."""
from django.db import models
from .abstracts import HasName, HasDescription, Modification
from .document import FromDocument

class FeatureItem(Modification):
    """This is the class for an individual class feature item, a subset of a class
    feature. The name field is unused."""

    feature = models.ForeignKey('Feature', on_delete=models.CASCADE)
    level = models.ForeignKey('Level', on_delete=models.CASCADE)

class Feature(HasName, HasDescription, FromDocument):
    """This class represents an individual class feature, such as Rage, or Extra
    Attack."""

    character_class = models.ForeignKey('Class', on_delete=models.CASCADE)

class Level(models.Model):
    """This is an individual level of a character class."""
    character_class = models.ForeignKey('Class', on_delete=models.CASCADE)


class Class(HasName, FromDocument):
    """The model for a character class or subclass."""
    subclass_of = models.ForeignKey('self',
                                   default=None,
                                   blank=True,
                                   null=True,
                                   on_delete=models.CASCADE)
    
    @property
    def is_subclass(self):
        """Returns whether the object is a subrace."""
        return self.subclass_of is not None

    @property
    def levels(self):
        """Returns the set of traits that are related to this race."""
        return self.level_set

    @property
    def features(self):
        """Returns the set of traits that are related to this race."""
        return self.feature_set