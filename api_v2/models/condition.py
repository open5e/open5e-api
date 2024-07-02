"""The model for a condition."""
from django.db import models

from .abstracts import HasName, HasDescription
from .document import FromDocument

class Condition(HasName, HasDescription, FromDocument):
    """
    This is the model for a condition.
    """

    class Meta:
        """To assist with the UI layer."""

        verbose_name_plural = "conditions"
