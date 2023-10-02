"""
The initialization for models for open5e's api v2.
"""

from .abstracts import HasName
from .abstracts import HasDescription
from .abstracts import Object

from .abilities import Abilities

from .item import Item
from .item import ItemSet

from .armor import Armor

from .weapon import Weapon

from .creature import Creature
from .creature import CreatureAction
from .creature import CreatureAttack

from .document import Document
from .document import License
from .document import Publisher
from .document import Ruleset
from .document import FromDocument
