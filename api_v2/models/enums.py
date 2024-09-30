
# Standard set of dice used in 5e.
DIE_TYPES = [
    ("D4", "d4"),
    ("D6", "d6"),
    ("D8", "d8"),
    ("D10", "d10"),
    ("D12", "d12"),
    ("D20", "d20"),
]

DISTANCE_UNIT_TYPES = [
    ("feet","feet"),
    ("miles","miles")
]

ABILITY_SCORE_MAXIMUM = 50
SAVING_THROW_MINIMUM = -5
SAVING_THROW_MAXIMUM = +20
SKILL_BONUS_MINIMUM = -5
SKILL_BONUS_MAXIMUM = +20
PASSIVE_SCORE_MAXIMUM = 40

# Setting a reasonable maximum for AC.
OBJECT_ARMOR_CLASS_MAXIMUM = 100

# Setting a reasonable maximum for HP.
OBJECT_HIT_POINT_MAXIMUM = 10000

# Senses available to a creature.
CREATURE_SENSES = [
    'blindsight',
    'truesight',
    'darkvision',
    'tremorsense'
]

# Type of creature attacks.
CREATURE_ATTACK_TYPES = [
    ("SPELL", "Spell"),
    ("WEAPON", "Weapon"),
]

ACTION_TYPES = [
    ("ACTION", "Action"),
    ("REACTION","Reaction"),
    ("BONUS_ACTION","Bonus Action"),
    ("LEGENDARY_ACTION","Legendary Action"),
    ("LAIR_ACTION","Lair Action")
]

# Monster action uses description.
CREATURE_USES_TYPES = [
    ("PER_DAY", "X/Day"),
    ("RECHARGE_ON_ROLL", "Recharge X-6"),
    ("RECHARGE_AFTER_REST", "Recharge after a Short or Long rest"),
]

# Spell options
SPELL_TARGET_TYPE_CHOICES = [
    ('creature',"Creature"),
    ('object',"Object"),
    ('point',"Point"),
    ('area',"Area")
]

MODIFICATION_TYPES = [
    ("ability_score", "Ability Score Increase or Decrease"),
    ("skill_proficiency", "Skill Proficiency"),
    ("tool_proficiency", "Tool Proficiency"),
    ("language", "Language"),
    ("equipment", "Equipment"),
    ("feature", "Feature"),  # Used in Backgrounds
    ("suggested_characteristics", "Suggested Characteristics"),  # Used in Backgrounds
    ("adventures_and_advancement", "Adventures and Advancement"),  # Used in A5e Backgrounds
    ("connection_and_memento", "Connection and Memento")]  # Used in A5e Backgrounds

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

SPELL_EFFECT_DURATIONS = [
    ("instantaneous","instantaneous"),
    ("instantaneous or special","instantaneous or special"),
    ("1 turn","1 turn"),
    ("1 round","1 round"),
    ("concentration + 1 round","concentration + 1 round"),
    ("2 rounds","2 rounds"),
    ("3 rounds","3 rounds"),
    ("4 rounds","4 rounds"),
    ("1d4+2 rounds","1d4+2 rounds"),
    ("5 rounds","5 rounds"),
    ("6 rounds","6 rounds"),
    ("10 rounds","10 rounds"),
    ("up to 1 minute","up to 1 minute"),
    ("1 minute","1 minute"),
    ("1 minute, or until expended","1 minute, or until expended"),
    ("1 minute, until expended","1 minute, until expended"),
    ("1 minute","1 minute"),
    ("5 minutes","5 minutes"),    
    ("10 minutes","10 minutes"),
    ("1 minute or 1 hour","1 minute or 1 hour"),
    ("up to 1 hour","up to 1 hour"),
    ("1 hour","1 hour"),
    ("1 hour or until triggered","1 hour or until triggered"),
    ("2 hours","2 hours"),
    ("3 hours","3 hours"),
    ("1d10 hours","1d10 hours"),
    ("6 hours","6 hours"),
    ("2-12 hours","2-12 hours"),
    ("up to 8 hours","up to 8 hours"),
    ("8 hours","8 hours"),
    ("1 hour/caster level","1 hour/caster level"),
    ("10 hours","10 hours"),
    ("12 hours","12 hours"),
    ("24 hours or until the target attempts a third death saving throw","24 hours or until the target attempts a third death saving throw"),
    ("24 hours","24 hours"),
    ("1 day","1 day"),
    ("3 days","3 days"),
    ("5 days","5 days"),
    ("7 days","7 days"),
    ("10 days","10 days"),
    ("13 days","13 days"),
    ("30 days","30 days"),
    ("1 year","1 year"),
    ("special","special"),
    ("until dispelled or destroyed","until dispelled or destroyed"),
    ("until destroyed","until destroyed"),
    ("until dispelled","until dispelled"),
    ("until cured or dispelled","until cured or dispelled"),
    ("until dispelled or triggered","until dispelled or triggered"),
    ("permanent until discharged","permanent until discharged"),
    ("permanent; one generation","permanent; one generation"),
    ("permanent","permanent"),
]

SPELL_CASTING_TIME_CHOICES = [
    ('reaction',"Reaction"),
    ('bonus-action',"1 Bonus Action"),
    ('action',"1 Action"),
    ('turn',"1 Turn"),
    ('round',"1 Round"),
    ('1minute',"1 Minute"),
    ('5minutes',"5 Minutes"),
    ('10minutes',"10 Minutes"),
    ('1hour',"1 Hour"),
    ('4hours',"4 Hours"),
    ('7hours',"7 Hours"),
    ('8hours',"8 Hours"),
    ('9hours',"9 Hours"),
    ('12hours',"12 Hours"),
    ('24hours',"24 Hours"),
    ('1week',"1 Week")
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
