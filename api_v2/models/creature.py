"""The model for a creature."""

from .abstracts import Object, HasDescription
from .document import FromDocument


class Creature(Object, HasDescription, FromDocument):
    """
    This is the model for a Creature, per the 5e ruleset.

    This extends the object model.
    """

    pass
