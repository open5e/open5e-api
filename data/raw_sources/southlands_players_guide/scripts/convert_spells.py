#!/usr/bin/env python3
"""
Southlands Player's Guide Spell Converter

Converts extracted spell markdown to Open5e API v2 JSON format.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

SCRIPT_DIR = Path(__file__).parent
RAW_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = RAW_DIR / "output"
DATA_V2_DIR = RAW_DIR.parent.parent / "v2" / "kobold-press" / "spg"

# Document key for Southlands Player's Guide
DOC_KEY = "spg"


def slugify(name: str) -> str:
    """Convert a name to a slug."""
    slug = name.lower()
    slug = re.sub(r"[''']", "", slug)
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug


def parse_level(level_text: str) -> int:
    """Parse spell level from text like '1st-level' or 'Cantrip'."""
    level_text = level_text.lower().strip()
    if "cantrip" in level_text:
        return 0
    match = re.search(r"(\d+)", level_text)
    if match:
        return int(match.group(1))
    return 0


def parse_school(school_text: str) -> str:
    """Parse spell school."""
    schools = [
        "abjuration", "conjuration", "divination", "enchantment",
        "evocation", "illusion", "necromancy", "transmutation"
    ]
    school_text = school_text.lower()
    for school in schools:
        if school in school_text:
            return school
    return "evocation"  # default


def parse_classes(class_text: str) -> List[str]:
    """Parse class list from parenthetical text.

    Note: For Kobold Press content, we store classes as empty arrays
    to match the existing data pattern. The class associations are
    documented in the spell description instead.
    """
    # Kobold Press pattern uses empty classes array
    # The classes are mentioned in the level_line for reference but not stored
    return []


def parse_casting_time(text: str) -> Tuple[str, Optional[str]]:
    """Parse casting time and extract reaction condition."""
    text = text.strip()

    if "reaction" in text.lower():
        # Extract reaction condition
        condition_match = re.search(r"reaction[,\s]+(?:which you take\s+)?(.+)", text, re.IGNORECASE)
        if condition_match:
            condition = condition_match.group(1).strip()
            # Clean up condition
            condition = re.sub(r"^when\s+", "", condition, flags=re.IGNORECASE)
            return "reaction", condition
        return "reaction", None

    if "bonus action" in text.lower():
        return "bonus_action", None

    if "minute" in text.lower():
        match = re.search(r"(\d+)\s*minute", text.lower())
        if match:
            return f"{match.group(1)}minutes", None
        return "10minutes", None

    if "hour" in text.lower():
        match = re.search(r"(\d+)\s*hour", text.lower())
        if match:
            return f"{match.group(1)}hours", None
        return "hour", None

    return "action", None


def parse_range(text: str) -> Tuple[float, Optional[str], str]:
    """Parse range value, unit, and text.

    Returns: (range_value, range_unit, range_text)
    range_text must be one of the SPELL_TARGET_RANGE_CHOICES:
    Self, Touch, Special, 5 feet, 10 feet, 15 feet, 20 feet, 25 feet,
    30 feet, 40 feet, 50 feet, 60 feet, 90 feet, 100 feet, 120 feet,
    150 feet, 300 feet, 500 feet, 1 mile, 500 miles, Sight, Unlimited
    """
    text = text.strip()

    if text.lower() == "self":
        return 0, None, "Self"
    if text.lower() == "touch":
        return 0, None, "Touch"

    # Extract numeric range in feet
    match = re.search(r"(\d+)\s*feet", text.lower())
    if match:
        feet = int(match.group(1))
        # Map to valid choices
        valid_feet = [5, 10, 15, 20, 25, 30, 40, 50, 60, 90, 100, 120, 150, 300, 500]
        # Find closest valid value
        closest = min(valid_feet, key=lambda x: abs(x - feet))
        return float(feet), "feet", f"{closest} feet"

    # Extract mile range
    match = re.search(r"(\d+)\s*mile", text.lower())
    if match:
        miles = int(match.group(1))
        return float(miles * 5280), "feet", f"{miles} mile" if miles == 1 else "500 miles"

    return 0, None, "Special"


def parse_components(text: str) -> Tuple[bool, bool, bool, str, Optional[int], bool]:
    """Parse components: V, S, M, material_specified, material_cost, material_consumed."""
    text = text.strip()

    verbal = "V" in text.upper().split(",")[0] if "V" in text.upper() else False
    # Be more careful about detecting V/S
    parts = text.upper().replace(",", " ").split()
    verbal = "V" in parts
    somatic = "S" in parts
    material = "M" in parts

    material_specified = ""
    material_cost = None
    material_consumed = False

    if material:
        # Extract material from parentheses
        mat_match = re.search(r"M\s*\(([^)]+)\)", text, re.IGNORECASE)
        if mat_match:
            material_specified = mat_match.group(1).strip()

            # Check for cost
            cost_match = re.search(r"(\d+)\s*gp", material_specified)
            if cost_match:
                material_cost = int(cost_match.group(1))

            # Check if consumed
            if "consume" in material_specified.lower():
                material_consumed = True

    return verbal, somatic, material, material_specified, material_cost, material_consumed


def parse_duration(text: str) -> Tuple[str, bool]:
    """Parse duration and concentration flag."""
    text = text.strip()
    concentration = "concentration" in text.lower()

    if "instantaneous" in text.lower():
        return "instantaneous", concentration

    # Extract duration
    duration_text = text.lower()

    # Handle "Concentration, up to X"
    if concentration:
        duration_text = re.sub(r"concentration[,\s]+(?:up to\s+)?", "", duration_text, flags=re.IGNORECASE)

    # Parse time
    time_match = re.search(r"(\d+)\s*(round|minute|hour|day|week)", duration_text)
    if time_match:
        num = time_match.group(1)
        unit = time_match.group(2)
        if unit == "round":
            return f"{num} round" if num == "1" else f"{num} rounds", concentration
        return f"{num} {unit}" if num == "1" else f"{num} {unit}s", concentration

    return duration_text.strip(), concentration


def extract_damage_info(desc: str) -> Tuple[str, List[str], str]:
    """Extract damage roll, damage types, and saving throw from description."""
    damage_roll = ""
    damage_types = []
    saving_throw = ""

    # Common damage types
    dmg_types = [
        "acid", "bludgeoning", "cold", "fire", "force", "lightning",
        "necrotic", "piercing", "poison", "psychic", "radiant", "slashing", "thunder"
    ]

    # Find damage dice
    dice_match = re.search(r"(\d+d\d+(?:\s*\+\s*\d+)?)", desc)
    if dice_match:
        damage_roll = dice_match.group(1).replace(" ", "")

    # Find damage types
    desc_lower = desc.lower()
    for dmg_type in dmg_types:
        if dmg_type in desc_lower:
            damage_types.append(dmg_type)

    # Find saving throw
    save_match = re.search(r"(Strength|Dexterity|Constitution|Intelligence|Wisdom|Charisma)\s+saving throw", desc, re.IGNORECASE)
    if save_match:
        saving_throw = save_match.group(1).lower()[:3]  # str, dex, con, int, wis, cha

    return damage_roll, damage_types, saving_throw


def has_attack_roll(desc: str) -> bool:
    """Check if spell involves an attack roll."""
    attack_phrases = [
        "make a melee spell attack",
        "make a ranged spell attack",
        "spell attack roll",
        "melee spell attack",
        "ranged spell attack",
    ]
    desc_lower = desc.lower()
    return any(phrase in desc_lower for phrase in attack_phrases)


def determine_target_type(desc: str, range_text: str) -> str:
    """Determine target type from description.

    Valid choices: creature, object, point, area
    """
    desc_lower = desc.lower()

    # Check for area effects
    area_keywords = ["cone", "sphere", "cube", "line", "cylinder", "radius", "area"]
    if any(kw in desc_lower for kw in area_keywords):
        return "area"

    # Check for point targeting
    if "point" in desc_lower or "location" in desc_lower:
        return "point"

    # Check for object targeting
    if "object" in desc_lower and "creature" not in desc_lower:
        return "object"

    # Default to creature for most spells
    return "creature"


# Manually defined spells from the PDF
SPELLS_RAW = [
    {
        "name": "Bat from the Sky",
        "level_line": "2nd-level evocation (druid, paladin, ranger)",
        "casting_time": "1 action, or 1 reaction when a flying creature moves adjacent to you",
        "range": "Touch",
        "components": "V, S",
        "duration": "Instantaneous",
        "desc": "You target a flying creature you can reach when you cast this spell. The creature must succeed on a Strength saving throw or be knocked prone and become stunned until the end of its next turn. If you use an action to cast this spell, you can use a bonus action to make a melee weapon attack against the target regardless of the result of its saving throw. If you cast this spell using your reaction, the creature has disadvantage on its saving throw.",
        "higher_level": "When you cast this spell using a spell slot of 4th level or higher, you can target an additional creature for each 2 slot levels above 2nd."
    },
    {
        "name": "Body Twist",
        "level_line": "1st-level transmutation (druid, ranger)",
        "casting_time": "1 reaction, which you take when you are grappled or restrained by a creature or physical object",
        "range": "Self",
        "components": "S",
        "duration": "Instantaneous",
        "desc": "When you cast this spell, your body contorts to allow you to maneuver out of a creature's grasp or bonds placed upon you. You can attempt to escape from a grapple or being restrained, you can use your spell attack roll in place of your ability check to escape, and you have advantage on the escape check.",
        "higher_level": "When you cast this spell using a spell slot of 2nd level or higher, you can instead target a creature within 30 feet of you, which can use its reaction to attempt to escape."
    },
    {
        "name": "Broken Wing",
        "level_line": "1st-level evocation (ranger, sorcerer, warlock, wizard)",
        "casting_time": "1 action",
        "range": "60 feet",
        "components": "V, S, M (a shed cat's claw)",
        "duration": "Instantaneous",
        "desc": "You take an imaginary swipe at a target within range as you cast this spell. The target must make a Constitution saving throw. On a failed save, it takes 2d6 slashing damage and reduces either its flying or walking speed (your choice) by 10 feet. On a success, it takes half damage and its speed is not reduced. If the target regains 5 hit points, the reduction to its speed ends.",
        "higher_level": "If you cast this spell using a spell slot of 2nd level or higher, the damage increases by 1d6 for each slot level above 1st, and you reduce the target's speed by an additional 5 feet for each slot level above 1st (to a maximum of 30 feet)."
    },
    {
        "name": "Pounce Strike",
        "level_line": "1st-level transmutation (ranger)",
        "casting_time": "1 action",
        "range": "Self",
        "components": "V",
        "duration": "1 round",
        "desc": "As part of the action to cast this spell, you can leap up to 15 feet in any direction, which does not provoke opportunity attacks, and make a melee spell attack. If this attack hits, the target suffers 2d8 force damage, and if the target is Large or smaller, it falls prone.",
        "higher_level": "When you cast this spell using a spell slot of 2nd level or higher, the damage increases by 1d8 per slot level above 1st."
    },
    {
        "name": "Warning Whiskers",
        "level_line": "2nd-level abjuration (druid, ranger, warlock)",
        "casting_time": "1 action",
        "range": "Touch",
        "components": "V, S, M (a cat's whisker)",
        "duration": "Concentration, up to 1 hour",
        "desc": "Thin, invisible fibers stretch from your cheeks (or your shoulders, sides, or thighs, as you prefer). These long whiskers reach up to 10 feet. For the spell's duration, you gain a +5 bonus to your passive Wisdom (Perception) score. Additionally, you know the location of invisible creatures within range of the whiskers. This negates advantage they have on their attack rolls against you, but your attack rolls still have disadvantage. You can target invisible creatures within 10 feet with spells that require you to be able to see the target. The whiskers also confer some stability to your movement. You have advantage on Dexterity checks made to maintain your balance or remain upright.",
        "higher_level": ""
    },
    {
        "name": "Alter Arrow's Fortune",
        "level_line": "1st-level divination (bard, cleric, druid, ranger, sorcerer, wizard)",
        "casting_time": "1 reaction, when an enemy makes a ranged attack that hits",
        "range": "100 feet",
        "components": "S",
        "duration": "Instantaneous",
        "desc": "You clap your hands, setting off a chain of tiny events that culminate in throwing off an enemy's aim. When an enemy makes a ranged attack (weapon or spell) that hits one of your allies, this spell causes the enemy to repeat the attack roll unless the enemy makes a successful Charisma saving throw. The attack is resolved using the lower of the two rolls (effectively giving the enemy disadvantage on the attack).",
        "higher_level": ""
    },
    {
        "name": "Anticipate Attack",
        "level_line": "2nd-level divination (bard, cleric, druid, paladin, ranger, sorcerer, wizard)",
        "casting_time": "1 reaction, when you are attacked but before the attack roll is made",
        "range": "Self",
        "components": "V, S",
        "duration": "Instantaneous",
        "desc": "In a flash of foreknowledge, you spot an oncoming attack with enough time to avoid it. Upon casting this spell, you can move up to half your speed without triggering opportunity attacks. The attack still occurs but misses automatically if you are no longer within the attack's range, are impossible for the attack to hit, or can't be targeted by that attack in your new position. If none of those apply but the situation has changed—you've moved into a position with cover, for example—then the attack is made under those new conditions.",
        "higher_level": ""
    },
    {
        "name": "Anticipate Arcana",
        "level_line": "3rd-level divination (cleric, paladin, sorcerer, warlock, wizard)",
        "casting_time": "1 reaction, when an enemy you can see casts a spell",
        "range": "Self",
        "components": "V, S",
        "duration": "Instantaneous",
        "desc": "Your foresight gives you an instant to ready your defenses against a magical attack. When you cast anticipate arcana, you have advantage on saving throws against spells and other magical effects until the start of your next turn.",
        "higher_level": ""
    },
    {
        "name": "Anticipate Weakness",
        "level_line": "1st-level divination (bard, cleric, druid, ranger, sorcerer, wizard)",
        "casting_time": "1 bonus action",
        "range": "Self",
        "components": "V, S",
        "duration": "Instantaneous",
        "desc": "With a quick glance into the future, you pinpoint where a gap is about to open in your foe's defense and then you strike. Upon casting anticipate weakness, you have advantage on attack rolls until the end of your turn.",
        "higher_level": ""
    },
    {
        "name": "Avoid Grievous Injury",
        "level_line": "2nd-level divination (bard, cleric, druid, sorcerer, warlock, wizard)",
        "casting_time": "1 reaction, when you are struck by a critical hit",
        "range": "Self",
        "components": "V, S",
        "duration": "Instantaneous",
        "desc": "You cast this spell when a foe strikes you with a critical hit but before damage dice are rolled. The critical hit against you becomes a normal hit.",
        "higher_level": ""
    },
    {
        "name": "Distraction Cascade",
        "level_line": "2nd-level divination (bard, cleric, druid, ranger, sorcerer, warlock, wizard)",
        "casting_time": "1 reaction, when an ally declares an attack against an enemy you can see",
        "range": "30 feet",
        "components": "V, S",
        "duration": "Instantaneous",
        "desc": "With a flash of foresight, you throw a foe off balance. Target one creature you can see that your ally has just declared as the target of an attack. Unless that creature makes a successful Charisma saving throw, attacks against it are made with advantage until the start of your next turn.",
        "higher_level": ""
    },
    {
        "name": "Distracting Divination",
        "level_line": "2nd-level divination (bard, cleric, sorcerer, warlock, wizard)",
        "casting_time": "1 reaction, when an enemy attempts to cast a spell",
        "range": "Touch",
        "components": "V, S",
        "duration": "Instantaneous",
        "desc": "Foresight tells you when and how to be just distracting enough to foil an enemy spellcaster. When an adjacent enemy attempts to cast a spell, make a melee spell attack against that enemy. If it hits, the enemy's spell fails and has no effect; the enemy's action is used up but the spell slot isn't expended.",
        "higher_level": ""
    },
    {
        "name": "Energy Foreknowledge",
        "level_line": "4th-level divination (bard, cleric, druid, sorcerer, wizard)",
        "casting_time": "1 reaction, when you are the target of a spell that does cold, fire, force, lightning, necrotic, psychic, radiant, or thunder damage",
        "range": "Self",
        "components": "V, S",
        "duration": "Instantaneous",
        "desc": "When you cast energy foreknowledge, you gain resistance to every type of energy listed above that's inflicted by the spell hitting you. This resistance lasts until the end of your next turn.",
        "higher_level": "When energy foreknowledge is cast with a spell slot of 5th level or higher, you can include one additional ally in its effect for each slot level above 4th. Affected allies must be within 15 feet of you."
    },
    {
        "name": "Foretell Distraction",
        "level_line": "1st-level divination (bard, cleric, ranger, sorcerer, warlock, wizard)",
        "casting_time": "1 bonus action",
        "range": "Self",
        "components": "S",
        "duration": "Instantaneous",
        "desc": "Thanks to your foreknowledge, you know just when your foe will take his or her eyes off you. Casting this spell has the same effect as making a successful Dexterity (Stealth) check, provided cover or concealment is accessible within 10 feet of you. It doesn't matter whether enemies can see you when you cast the spell; they glance away at just the right moment. You can move up to 10 feet as part of casting the spell, provided you're able to move (not restrained or grappled or reduced to a speed less than 10 for any other reason). This doesn't count as part of your normal movement. After the spell is cast, you must be in a position where you can remain hidden: a lightly obscured space, for example, or a space where you have total cover. Otherwise, enemies see you again immediately and you're not hidden.",
        "higher_level": ""
    },
    {
        "name": "Heartstrike",
        "level_line": "2nd-level divination (druid, ranger)",
        "casting_time": "1 bonus action",
        "range": "Self",
        "components": "V, S, M (an arrow, bolt, or other missile)",
        "duration": "Instantaneous",
        "desc": "The spirits of ancient archers carry your missiles straight to their targets. You have advantage on ranged weapon attacks until the start of your next turn, and you can ignore penalties for half cover, three-quarters cover, and light obscuration when making those attacks.",
        "higher_level": ""
    },
    {
        "name": "Insightful Maneuver",
        "level_line": "1st-level divination (cleric, paladin, ranger, sorcerer, warlock, wizard)",
        "casting_time": "1 bonus action",
        "range": "Touch",
        "components": "V, S",
        "duration": "Instantaneous",
        "desc": "With a flash of insight, you can take advantage of your foe's vulnerabilities. Until the end of your turn, the target has vulnerability to one type of damage (your choice). Additionally, if the target has any other vulnerabilities, you learn them.",
        "higher_level": ""
    },
    {
        "name": "Litany of Sure Hands",
        "level_line": "1st-level divination (paladin)",
        "casting_time": "1 bonus action",
        "range": "30 feet",
        "components": "V, S",
        "duration": "1 minute",
        "desc": "This litany allows the recipient to perform clumsy tasks with speed and alacrity. The target of the litany ignores the loading property of weapons and can drink a potion as a bonus action for the duration of the spell.",
        "higher_level": ""
    },
    {
        "name": "Scry Ambush",
        "level_line": "3rd-level divination (bard, cleric, druid, ranger, sorcerer, warlock, wizard)",
        "casting_time": "1 reaction, taken at the start of an enemy's turn",
        "range": "Self",
        "components": "V, S",
        "duration": "Instantaneous",
        "desc": "You foresee your foe's attack a split second before it begins. When you cast this spell, a number of your allies equal to your spellcasting ability modifier (minimum of 1) + your proficiency bonus are not surprised. If you yourself were surprised, you must make a spellcasting check at the moment your reaction should be triggered. The DC equals the initiative number of the current turn. If the spellcasting check fails, you remain surprised and can't use a reaction to cast the spell until after your turn. If the check succeeds, you can take a reaction to cast the spell but you must be one of its targets.",
        "higher_level": ""
    },
    {
        "name": "Seer's Reaction",
        "level_line": "1st-level divination (bard, cleric, druid, ranger, sorcerer, wizard)",
        "casting_time": "1 reaction, at the start of any other creature's turn",
        "range": "Self",
        "components": "V, S",
        "duration": "Instantaneous",
        "desc": "Your foreknowledge allows you to act before others because you knew this was going to happen. When you cast this spell, reroll your Dexterity check for initiative with a +5 bonus. Your initiative equals the higher of the two results. If that number is higher than the current initiative number, take your turn immediately but switch to the higher number next round.",
        "higher_level": ""
    },
    {
        "name": "Sidestep Arrow",
        "level_line": "3rd-level divination (bard, cleric, druid, ranger, sorcerer, warlock, wizard)",
        "casting_time": "1 reaction, when an enemy targets you with a ranged attack",
        "range": "Self",
        "components": "V, S",
        "duration": "Instantaneous",
        "desc": "With a few perfectly timed steps, you maneuver a foe between you and danger. You can cast this spell when a foe targets you with a ranged attack but before the attack roll is made, the spell is cast, etc. At least one other foe must be within 10 feet of you when you cast sidestep arrow. As part of casting the spell, you can move up to 15 feet to place an enemy between you and the attacker, in the direct line of attack. You must be able to move (not restrained or grappled or reduced to speed 0 for any other reason). This move does not provoke opportunity attacks. After you've moved, the ranged attack is resolved with the intervening foe as the target instead of you.",
        "higher_level": ""
    },
    {
        "name": "Slippery Fingers",
        "level_line": "1st-level divination (bard, cleric, druid, sorcerer, warlock, wizard)",
        "casting_time": "1 bonus action",
        "range": "30 feet",
        "components": "V, S",
        "duration": "Instantaneous",
        "desc": "You set a series of small events in motion that cause the targeted creature to drop one nonmagical item of your choice that it's currently holding unless it makes a successful Charisma saving throw. This spell can't cause magic items to be dropped.",
        "higher_level": ""
    },
    {
        "name": "Soothsayer's Shield",
        "level_line": "2nd-level divination (bard, cleric, druid, ranger)",
        "casting_time": "1 reaction, when you are hit by an attack",
        "range": "Self",
        "components": "V, S",
        "duration": "Instantaneous",
        "desc": "This spell can be cast when you are hit by an enemy's attack. Until the start of your next turn, you have a +4 bonus to AC, including against the triggering attack.",
        "higher_level": ""
    },
    {
        "name": "Targeting Foreknowledge",
        "level_line": "3rd-level divination (bard, cleric, druid, ranger, sorcerer, wizard)",
        "casting_time": "1 bonus action",
        "range": "Self",
        "components": "V",
        "duration": "Instantaneous",
        "desc": "Twisting the knife, slapping with the butt of the spear, cutting again as you recover from a lunge, and countless other double-strike maneuvers are skillful ways to get more from your weapon. By casting this spell as a bonus action after making a successful melee weapon attack, you inflict an additional 2d6 damage of the weapon's type to the target. If your attack roll was a natural 19, the attack becomes a critical hit and you also add the weapon's basic damage die or dice (the normal damage boost for a critical hit) to the 2d6 bonus damage, along with any other special result you would normally cause with a critical hit.",
        "higher_level": ""
    },
    {
        "name": "Twist the Skein",
        "level_line": "1st-level divination (cleric, warlock)",
        "casting_time": "1 reaction, when a creature makes a successful or unsuccessful attack roll, saving throw, or skill check",
        "range": "30 feet",
        "components": "S",
        "duration": "Instantaneous",
        "desc": "You tweak a strand of a creature's fate as it makes an attack roll, saving throw, or skill check. Roll 1d20 - 10 to produce a number from 10 to -9. Add that number to the creature's roll, increasing or decreasing the result accordingly. This adjustment can turn a failure into a success or vice versa, or it may not change the outcome at all. The target must use the modified result regardless of whether it's better or worse than the original.",
        "higher_level": ""
    },
]


def convert_spell(spell_data: Dict) -> Dict[str, Any]:
    """Convert a raw spell entry to Open5e V2 format."""
    name = spell_data["name"]
    level_line = spell_data["level_line"]

    # Parse level and school from level line
    # Format: "1st-level evocation (bard, cleric)"
    level_match = re.match(r"(Cantrip|\d+(?:st|nd|rd|th)-level)\s+(\w+)", level_line, re.IGNORECASE)
    level = 0
    school = "evocation"
    if level_match:
        level = parse_level(level_match.group(1))
        school = parse_school(level_match.group(2))

    # Parse classes from parentheses in level line
    classes_match = re.search(r"\(([^)]+)\)", level_line)
    classes = []
    if classes_match:
        classes = parse_classes(classes_match.group(1))

    # Parse other fields
    casting_time, reaction_condition = parse_casting_time(spell_data["casting_time"])
    range_val, range_unit, range_text = parse_range(spell_data["range"])
    verbal, somatic, material, material_specified, material_cost, material_consumed = parse_components(spell_data["components"])
    duration, concentration = parse_duration(spell_data["duration"])

    # Check for ritual
    ritual = "ritual" in level_line.lower()

    # Extract damage info from description
    damage_roll, damage_types, saving_throw = extract_damage_info(spell_data["desc"])
    attack_roll = has_attack_roll(spell_data["desc"])

    # Determine target type
    target_type = determine_target_type(spell_data["desc"], range_text)

    # Build the spell entry
    spell_entry = {
        "model": "api_v2.spell",
        "pk": f"{DOC_KEY}_{slugify(name)}",
        "fields": {
            "name": name,
            "desc": spell_data["desc"],
            "higher_level": spell_data.get("higher_level", ""),
            "document": DOC_KEY,
            "level": level,
            "school": school,
            "casting_time": casting_time,
            "reaction_condition": reaction_condition,
            "range": int(range_val),
            "range_text": range_text,
            "range_unit": range_unit,
            "ritual": ritual,
            "verbal": verbal,
            "somatic": somatic,
            "material": material,
            "material_specified": material_specified,
            "material_cost": material_cost,
            "material_consumed": material_consumed,
            "concentration": concentration,
            "duration": duration,
            "target_type": target_type,
            "target_count": 1,  # Default to 1 target
            "saving_throw_ability": saving_throw if saving_throw else "",
            "attack_roll": attack_roll,
            "damage_roll": damage_roll,
            "damage_types": damage_types,
            "shape_type": None,
            "shape_size": None,
            "shape_size_unit": None,
            "classes": classes,
        }
    }

    return spell_entry


def main():
    print("=" * 60)
    print("Southlands Player's Guide Spell Converter")
    print("=" * 60)

    print(f"\nConverting {len(SPELLS_RAW)} spells...")

    spells = []
    for spell_data in SPELLS_RAW:
        spell = convert_spell(spell_data)
        spells.append(spell)
        print(f"  - {spell['fields']['name']} ({spell['fields']['level']}, {spell['fields']['school']})")

    # Create output directory
    DATA_V2_DIR.mkdir(parents=True, exist_ok=True)

    # Write spells JSON
    spells_path = DATA_V2_DIR / "Spell.json"
    with open(spells_path, "w", encoding="utf-8") as f:
        json.dump(spells, f, indent=2, ensure_ascii=False)
    print(f"\nSaved {len(spells)} spells to {spells_path}")

    # Also save to output dir for reference
    output_spells_path = OUTPUT_DIR / "Spell.json"
    with open(output_spells_path, "w", encoding="utf-8") as f:
        json.dump(spells, f, indent=2, ensure_ascii=False)
    print(f"Also saved to {output_spells_path}")

    print("\n" + "=" * 60)
    print("Conversion complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
