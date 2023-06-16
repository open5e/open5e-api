"""The model for a type of weapon."""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from .abstracts import HasName
from .document import FromDocument


class MagicItemType(HasName, FromDocument):
    """
    This model represents types of magic items.

    This does not represent a magic item itself, because that would be an item.
    """

    RARITY_CHOICES = [
        (1,'common'),
        (2,'uncommon'),
        (3,'rare'),
        (4,'very rare'),
        (5,'legendary')
    ]

    requires_attunement = models.BooleanField(
        null=False,
        default=False,  # An item is not magical unless specified.
        help_text='If the item requires attunement.')

    rarity = models.IntegerField(
        null=True,  # Allow an unspecified size.
        choices=RARITY_CHOICES,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5)],
        help_text='Integer representing the rarity of the object.')
