from django.db import models
from django.core.validators import MinValueValidator

from .abstracts import HasName
from .abstracts import distance_field
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

    space_diameter = distance_field()