"""The initialization for models for open5e's api v2."""

from .item import ItemCategory
from .item import Item
from .item import ItemSet
from .item import ItemRarity
from .abilities import Ability
from .abilities import Skill

from .armor import Armor

from .weapon import Weapon
from .weapon import WeaponProperty
from .weapon import WeaponPropertyAssignment

from .species import SpeciesTrait
from .species import Species

from .feat import FeatBenefit
from .feat import Feat

from .background import BackgroundBenefit
from .background import Background

from .creature import Creature
from .creature import CreatureTrait
from .creature import CreatureAction
from .creature import CreatureActionAttack
from .creature import CreatureType
from .creature import CreatureTypeDescription
from .creature import CreatureSet

from .document import Document
from .document import License
from .document import Publisher
from .document import GameSystem
from .document import FromDocument

from .damagetype import DamageType
from .damagetype import DamageTypeDescription

from .language import Language

from .alignment import Alignment
from .alignment import AlignmentDescription

from .condition import Condition
from .condition import ConditionConcept

from .spell import Spell
from .spell import SpellCastingOption
from .spell import SpellSchool

from .characterclass import ClassFeatureItem
from .characterclass import ClassFeature
from .characterclass import CharacterClass

from .size import Size

from .environment import Environment

from .speed import HasSpeed

from .rule import Rule, RuleSet

from .image import Image, HasIcon, HasIllustration

from .service import Service