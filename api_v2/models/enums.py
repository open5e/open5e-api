
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
    ('Self',"Self"),
    ('Touch',"Touch"),
    ('Special',"Special"),
    ('5 feet',"5 feet"),
    ('10 feet',"10 feet"),
    ('15 feet',"15 feet"),
    ('20 feet',"20 feet"),
    ('25 feet',"25 feet"),
    ('30 feet',"30 feet"),
    ('40 feet',"40 feet"),
    ('50 feet',"50 feet"),
    ('60 feet',"60 feet"),
    ('90 feet',"90 feet"),
    ('100 feet',"100 feet"),
    ('120 feet',"120 feet"),
    ('150 feet',"150 feet"),
    ('180 feet',"180 feet"),
    ('200 feet',"200 feet"),
    ('300 feet',"300 feet"),
    ('400 feet',"400 feet"),
    ('500 feet',"500 feet"),
    ('1000 feet',"1000 feet"),
    ('Sight',"Sight"),
    ('1 mile',"1 mile"),
    ('5 miles',"5 miles"),
    ('10 miles',"10 miles"),
    ('100 miles',"100 miles"),
    ('150 miles',"150 miles"),
    ('500 miles',"500 miles"),
    ('Unlimited',"Unlimited"),
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

CASTING_OPTION_TYPES = [
    ('default',"Default"),
    ('ritual','Ritual'),
    ('player_level_1','Player Level 1'),
    ('player_level_2','Player Level 2'),
    ('player_level_3','Player Level 3'),
    ('player_level_4','Player Level 4'),
    ('player_level_5','Player Level 5'),
    ('player_level_6','Player Level 6'),
    ('player_level_7','Player Level 7'),
    ('player_level_8','Player Level 8'),
    ('player_level_9','Player Level 9'),
    ('player_level_10','Player Level 10'),
    ('player_level_11','Player Level 11'),
    ('player_level_12','Player Level 12'),
    ('player_level_13','Player Level 13'),
    ('player_level_14','Player Level 14'),
    ('player_level_15','Player Level 15'),
    ('player_level_16','Player Level 16'),
    ('player_level_17','Player Level 17'),
    ('player_level_18','Player Level 18'),
    ('player_level_19','Player Level 19'),
    ('player_level_20','Player Level 20'),
    ('slot_level_1','Spell Slot Level 1'),
    ('slot_level_2','Spell SlotLevel 2'),
    ('slot_level_3','Spell Slot Level 3'),
    ('slot_level_4','Spell Slot Level 4'),
    ('slot_level_5','Spell Slot Level 5'),
    ('slot_level_6','Spell Slot Level 6'),
    ('slot_level_7','Spell Slot Level 7'),
    ('slot_level_8','Spell Slot Level 8'),
    ('slot_level_9','Spell Slot Level 9')
]