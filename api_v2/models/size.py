from django.db import models

from .abstracts import HasName
from .abstracts import distance_field, distance_unit_field, damage_die_type_field
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
    distance_unit = distance_unit_field()

    suggested_hit_dice = damage_die_type_field()

    @property
    def get_distance_unit(self):
        if self.distance_unit is None:
            return self.document.distance_unit
        return self.distance_unit
