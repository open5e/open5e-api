"""The model for a condition."""
from django.db import models

from .abstracts import HasName, HasDescription
from .document import FromDocument
from .image import HasIcon

class Condition(HasName, HasDescription, HasIcon, FromDocument):
    """
    This is the model for a condition.
    """

    class Meta:
        """To assist with the UI layer."""

        verbose_name_plural = "conditions"


class ConditionDescription(HasDescription, FromDocument):
    """A description of the condition."""
    describes = models.ForeignKey(Condition, on_delete=models.CASCADE)
