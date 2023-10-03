"""The model for a feat."""
from django.db import models
from .abstracts import HasName, HasDescription, Benefit
from .document import FromDocument


class BackgroundBenefit(Benefit):
    background = models.ForeignKey('Background', on_delete=models.CASCADE)


class Background(HasName, HasDescription, FromDocument):
    """
    This is the model for a character background.

    Your character's background reveals where you came from, how you became
    an adventurer, and your place in the world.
    """

    class Meta:
        """To assist with the UI layer."""

        verbose_name_plural = "backgrounds"
