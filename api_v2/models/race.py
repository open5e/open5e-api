"""The model for a race, subrace, and it's traits."""

from django.db import models
from .abstracts import HasName, HasDescription, HasPrerequisite
from .document import FromDocument


class Trait(HasName, HasDescription):
    """
    This is the model for a racial trait.

    Each trait ties to an individual race or subrace.
    """

    race = models.ForeignKey('Race', on_delete=models.CASCADE)


class Race(HasName, HasDescription, FromDocument):
    """
    This is the model for a race or subrace.

    This model can be used to represent races and subraces. Subraces are
    represented by using a self-relation to the parent race.
    """

    subrace_of = models.ForeignKey('self',
                                   default=None,
                                   blank=True,
                                   null=True,
                                   on_delete=models.CASCADE)

    @property
    def is_subrace(self):
        """Returns whether the object is a subrace."""
        return self.subrace_of is not None

    @property
    def traits(self):
        """Returns the set of traits that are related to this race."""
        return self.trait_set

    class Meta:
        """To assist with the UI layer."""

        verbose_name_plural = "races"
