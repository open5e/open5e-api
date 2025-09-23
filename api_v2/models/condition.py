"""The model for a condition."""
from django.db import models

from .abstracts import HasName, HasDescription
from .document import FromDocument
from .image import HasIcon

class Condition(HasName, HasIcon, FromDocument):
    """
    This is the model for a condition.
    """

    @property
    def descriptions(self):
        """ Gets the description based on parameter, and then if none, global priority"""
        return ConditionDescription.objects.filter(describes=self).all().order_by("pk")

    class Meta:
        """To assist with the UI layer."""

        verbose_name_plural = "conditions"


class ConditionDescription(HasDescription, FromDocument):
    """A description of the condition."""
    describes = models.ForeignKey(Condition, on_delete=models.CASCADE)
