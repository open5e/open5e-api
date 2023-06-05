"""The model for an item."""

from django.db import models
from api.models import GameContent


class Item(Object):
    """
    This is the model for an Item, which is an object that can be used.

    This extends the object model, but adds other concepts.
    """

    cost = models.DecimalField(
        null=True,  # Allow an unspecified cost.
        max_digits=10,
        decimal_places=2,  # Only track down to 2 decimal places.
        validators=[MinValueValidator(0)],
        help_text='Number representing the cost of the object.')

    is_magical = models.BooleanField(
        null=False,
        default=False,  # An item is not magical unless specified.
        help_text='If the item is a magical item.')
