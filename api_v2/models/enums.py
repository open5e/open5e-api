
# Standard set of dice used in 5e.
DIE_TYPES = [
    ("D4", "d4"),
    ("D6", "d6"),
    ("D8", "d8"),
    ("D10", "d10"),
    ("D12", "d12"),
    ("D20", "d20"),
]

# List of damage types possible in 5e.
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

# Enumerating sizes, so they are sortable.
OBJECT_SIZE_CHOICES = [
    (1, "Tiny"),
    (2, "Small"),
    (3, "Medium"),
    (4, "Large"),
    (5, "Huge"),
    (6, "Gargantuan")]

# Setting a reasonable maximum for AC.
OBJECT_ARMOR_CLASS_MAXIMUM = 100

# Setting a reasonable maximum for HP.
OBJECT_HIT_POINT_MAXIMUM = 10000

# Types of monsters, and their name spelling.
CREATURE_MONSTER_TYPES = [
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
CREATURE_ATTACK_TYPES = [
    ("SPELL", "Spell"),
    ("WEAPON", "Weapon"),
]


# Monster action uses description.
CREATURE_USES_TYPES = [
    ("PER_DAY", "X/Day"),
    ("RECHARGE_ON_ROLL", "Recharge X-6"),
    ("RECHARGE_AFTER_REST", "Recharge after a Short or Long rest"),
]

# Item Rarity
ITEM_RARITY_CHOICES = [
    (1, 'common'),
    (2, 'uncommon'),
    (3, 'rare'),
    (4, 'very rare'),
    (5, 'legendary'),
    (6, 'artifact')
]

# Spell options
SPELL_TARGET_TYPE_CHOICES = [
    ('creature',"Creature"),
    ('object',"Object"),
    ('point',"Point"),
    ('area',"Area")
]

SPELL_TARGET_RANGE_CHOICES = [
    ('self',"Self"),
    ('touch',"Touch"),
    ('special',"special"),
    ('5',"5 feet"),
    ('10',"10 feet"),
    ('15',"15 feet"),
    ('20',"20 feet"),
    ('25',"25 feet"),
    ('30',"30 feet"),
    ('40',"40 feet"),
    ('50',"50 feet"),
    ('60',"60 feet"),
    ('90',"90 feet"),
    ('100',"100 feet"),
    ('120',"120 feet"),
    ('150',"150 feet"),
    ('180',"180 feet"),
    ('200',"200 feet"),
    ('300',"300 feet"),
    ('400',"400 feet"),    
    ('500',"500 feet"),    
    ('1000',"1000 feet"),
    ('1mile',"1 mile"),
    ('5miles',"5 miles"),
    ('10miles',"10 miles"),
    ('100miles',"100 miles"),
    ('150miles',"150 miles"),
    ('500miles',"500 miles"),
    ('sight',"Sight"),
    ('unlimited',"Unlimited"),
]

SPELL_EFFECT_SHAPE_CHOICES = [
    ('cone',"Cone"),
    ('cube',"Cube"),
    ('cylinder',"Cylinder"),
    ('line',"Line"),
    ('sphere',"sphere"),
]

SPELL_CASTING_TIME_CHOICES = [
    ('reaction',"Reaction"),
    ('bonus-action',"1 Bonus Action"),
    ('action',"1 Action"),
    ('1minute',"1 Minute"),
    ('5minutes',"5 Minutes"),
    ('10minutes',"10 Minutes"),
    ('1hour',"1 Hour"),
    ('8hours',"8 Hours"),
]

SPELL_SCHOOL_CHOICES = [
    ('abjuration','Abjuration'),
    ('conjuration','Conjuration'),
    ('divination','Divination'),
    ('enchantment','Enchantment'),
    ('evocation','Evocation'),
    ('illusion','Illusion'),
    ('necromancy','Necromancy'),
    ('transmutation','Transmutaion'),
]