"""The model for a feat."""
from django.db import models
from .abstracts import HasName, HasDescription, HasPrerequisite, Modification
from .document import FromDocument

#TODO rename to FeatBenefit
class FeatBenefit(Modification):
    """This is the model for an individual benefit of a feat."""

    #TODO refactor to parent
    feat = models.ForeignKey('Feat', on_delete=models.CASCADE)


class Feat(HasName, HasDescription, HasPrerequisite, FromDocument):
    """
    This is the model for a feat.

    A feat represents a talent or an area of expertise that
    gives a character special capabilities. It embodies
    training, experience, and abilities beyond what a
    class provides.
    """

    @property
    def capabilities(self):
        """Returns the set of benefits that are related to this feat."""
        return self.capability_set

    class Meta:
        """To assist with the UI layer."""

        verbose_name_plural = "feats"
