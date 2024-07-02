"""The model for an environment."""
from django.db import models
from .abstracts import HasName, HasDescription
from .document import FromDocument

class Environment(HasName, HasDescription, FromDocument):
    """
    This is the model for an environment.

    An environment represents the description of a type of place within
    the 5e universe.
    """
    aquatic = models.BooleanField(
        help_text='Whether or not aquatic environment rules apply to this environment.',
        default=False)

    planar = models.BooleanField(
        help_text='Whether or not this environment is a plane of existence.',
        default=False)

    class Meta:
        """To assist with the UI layer."""

        verbose_name_plural = "environments"
