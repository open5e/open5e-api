"""The model for a creature."""

from .abilities import Abilities
from .abstracts import Object
from .document import FromDocument


class Creature(Object, Abilities, FromDocument):
    """
    This is the model for a Creature, per the 5e ruleset.

    This extends the object and abilities models.
    """

    pass
