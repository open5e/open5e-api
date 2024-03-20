from django.db import models
from django.core.validators import MinValueValidator

from .abstracts import HasName
from .document import FromDocument

class Size(HasName, FromDocument):
    """
    This is the definition of the Size class.

    The Size class will be used by Objects (and all children classes).
    Basically it describes the size.
    """

    rank = models.IntegerField(
        unique=True,
        help_text='Ranking of the size, smallest has the lowest values.')

    space_diameter = models.DecimalField(
        default=0,
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(0)],
        help_text='Number representing the diameter of the space controlled by the object.')
