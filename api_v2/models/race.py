"""The model for a race, subrace, and it's traits."""

from django.db import models
from .abstracts import HasName, HasDescription, HasPrerequisite
from .document import FromDocument


class Trait(HasName, HasDescription):
    """
    This is the model for a racial trait.

    Each trait ties to an individual race or subrace.
    """

    race = models.ForeignKey('Race')


class Race(HasName, HasDescription, FromDocument):
    """
    This is the model for a race or subrace.

    This model can be used to represent races based on parent=null.
    """

    parent = models.ForeignKey('self', null=True)

    @property
    def is_subrace(self):
        """Returns whether the object is a subrace."""
        return self.parent == null
