
# Standard set of dice used in 5e.
DIE_TYPES = [
    ("D4", "d4"),
    ("D6", "d6"),
    ("D8", "d8"),
    ("D10", "d10"),
    ("D12", "d12"),
    ("D20", "d20"),
]

# Enumerating sizes, so they are sortable.
SIZE_CHOICES = [
    (1, "Tiny"),
    (2, "Small"),
    (3, "Medium"),
    (4, "Large"),
    (5, "Huge"),
    (6, "Gargantuan")]

# Setting a reasonable maximum for AC.
ARMOR_CLASS_MAXIMUM = 100

# Setting a reasonable maximum for HP.
HIT_POINT_MAXIMUM = 10000

# Types of monsters, and their name spelling.
MONSTER_TYPES = [
    ("ABERRATION", "Aberration"),
    ("BEAST", "Beast"),
    ("CELESTIAL", "Celestial"),
    ("CONSTRUCT", "Construct"),
    ("DRAGON", "Dragon"),
    ("ELEMENTAL", "Elemental"),
    ("FEY", "Fey"),
    ("FIEND", "Fiend"),
    ("GIANT", "Giant"),
    ("HUMANOID", "Humanoid"),
    ("MONSTROSITY", "Monstrosity"),
    ("OOZE", "Ooze"),
    ("PLANT", "Plant"),
    ("UNDEAD", "Undead"),
]

# Type of creature attacks.
ATTACK_TYPES = [
    ("SPELL", "Spell"),
    ("WEAPON", "Weapon"),
]

DAMAGE_TYPES = [
    ("ACID", "Acid"),
    ("BLUDGEONING", "Bludgeoning"),
    ("COLD", "Cold"),
    ("FIRE", "Fire"),
    ("FORCE", "Force"),
    ("LIGHTNING", "Lightning"),
    ("NECROTIC", "Necrotic"),
    ("PIERCING", "Piercing"),
    ("POISON", "Poison"),
    ("PSYCHIC", "Psychic"),
    ("RADIANT", "Radiant"),
    ("SLASHING", "Slashing"),
    ("THUNDER", "Thunder"),
]

# Monster action uses description.
USES_TYPES = [
    ("PER_DAY", "X/Day"),
    ("RECHARGE_ON_ROLL", "Recharge X-6"),
    ("RECHARGE_AFTER_REST", "Recharge after a Short or Long rest"),
]

# Item Rarity
RARITY_CHOICES = [
    (1, 'common'),
    (2, 'uncommon'),
    (3, 'rare'),
    (4, 'very rare'),
    (5, 'legendary'),
    (6, 'artifact')
]
