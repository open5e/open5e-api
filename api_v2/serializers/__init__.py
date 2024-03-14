"""The initialization for serializers for open5e's api v2."""

from .item import ArmorSerializer
from .item import WeaponSerializer
from .item import ItemSerializer
from .item import ItemRaritySerializer
from .item import ItemSetSerializer
from .item import ItemCategorySerializer

from .background import BenefitSerializer
from .background import BackgroundSerializer

from .document import RulesetSerializer
from .document import LicenseSerializer
from .document import PublisherSerializer
from .document import DocumentSerializer

from .feat import CapabilitySerializer
from .feat import FeatSerializer

from .race import TraitSerializer
from .race import SubraceSerializer
from .race import RaceSerializer

from .creature import CreatureSerializer
from .creature import CreatureTypeSerializer

from .damagetype import DamageTypeSerializer

from .language import LanguageSerializer

from .alignment import AlignmentSerializer

from .condition import ConditionSerializer

from .spell import SpellSerializer

from .characterclass import CharacterClassSerializer
from .characterclass import FeatureSerializer
from .characterclass import FeatureItemSerializer
