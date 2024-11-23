"""The initialization for serializers for open5e's api v2."""

from .item import ArmorSerializer
from .item import WeaponSerializer
from .item import ItemSerializer
from .item import ItemRaritySerializer
from .item import ItemSetSerializer
from .item import ItemCategorySerializer

from .background import BackgroundBenefitSerializer
from .background import BackgroundSerializer

from .document import GameSystemSerializer
from .document import LicenseSerializer
from .document import PublisherSerializer
from .document import DocumentSerializer

from .feat import FeatBenefitSerializer
from .feat import FeatSerializer

from .race import RaceTraitSerializer
from .race import RaceSerializer

from .creature import CreatureSerializer
from .creature import CreatureTypeSerializer
from .creature import CreatureSetSerializer
from .creature import CreatureTraitSerializer

from .damagetype import DamageTypeSerializer

from .language import LanguageSerializer

from .alignment import AlignmentSerializer

from .condition import ConditionSerializer

from .spell import SpellSerializer, SpellSchoolSerializer

from .characterclass import CharacterClassSerializer
from .characterclass import ClassFeatureSerializer
from .characterclass import ClassFeatureItemSerializer

from .search import SearchResultSerializer

from .size import SizeSerializer

from .environment import EnvironmentSerializer

from .ability import AbilitySerializer
from .ability import SkillSerializer

from .rule import RuleSerializer, RuleSetSerializer