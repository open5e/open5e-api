"""The model for a creature."""

from django.db import models
from .abilities import Abilities
from .abstracts import Object, HasDescription, HasName
from .document import FromDocument


class Creature(Object, Abilities, FromDocument):
    """
    This is the model for a Creature, per the 5e ruleset.

    This extends the object and abilities models.
    """

    pass


USES_TYPES = [
    ("PER_DAY", "X/Day"),
    ("RECHARGE_ON_ROLL", "Recharge X-6"),
    ("RECHARGE_AFTER_REST", "Recharge after a Short or Long rest"),
]

class CreatureAction(HasName, HasDescription, FromDocument):

    creature = models.ForeignKey(
        Creature,
        on_delete=models.CASCADE,
        help_text='The creature to which this action belongs.'
    )

    uses_type = models.CharField(
        null=True,
        max_length=20,
        choices=USES_TYPES,
        help_text='How use of the action is limited, if at all.'
    )

    uses_param = models.SmallIntegerField(
        null=True,
        help_text='The parameter X for if the action is limited.'
    )
