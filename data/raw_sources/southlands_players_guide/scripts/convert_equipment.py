#!/usr/bin/env python3
"""
Southlands Player's Guide Equipment Converter

Converts weapon and item data to Open5e API v2 JSON format.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

SCRIPT_DIR = Path(__file__).parent
RAW_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = RAW_DIR / "output"
DATA_V2_DIR = RAW_DIR.parent.parent / "v2" / "kobold-press" / "spg"

DOC_KEY = "spg"


def slugify(name: str) -> str:
    """Convert a name to a slug."""
    slug = name.lower()
    slug = re.sub(r"[''']", "", slug)
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug


def parse_damage(damage_str: str) -> tuple[str, str]:
    """Parse damage string like '1d4 bludgeoning' into (dice, type)."""
    match = re.match(r"(\d+d\d+|\d+)\s+(\w+)", damage_str)
    if match:
        return match.group(1), match.group(2)
    return "0", "bludgeoning"


def parse_range(range_str: str) -> tuple[float, float]:
    """Parse range string like 'range 20/60' into (short, long)."""
    match = re.search(r"range\s+(\d+)/(\d+)", range_str, re.IGNORECASE)
    if match:
        return float(match.group(1)), float(match.group(2))
    return 0.0, 0.0


# Weapon data from the PDF - Simple Melee Weapons
SIMPLE_MELEE_WEAPONS = [
    {
        "name": "Rungu (throwing club)",
        "damage": "1d4 bludgeoning",
        "weight": "1 lb.",
        "cost": "2 gp",
        "properties": "Light, thrown (range 20/60)"
    },
    {
        "name": "Stabbing knife",
        "damage": "1d4 piercing",
        "weight": "1 lb.",
        "cost": "2 gp",
        "properties": "Finesse, light"
    },
]

# Martial Melee Weapons
MARTIAL_MELEE_WEAPONS = [
    {
        "name": "Bladed scarf",
        "damage": "1d4 slashing",
        "weight": "3 lb.",
        "cost": "100 gp",
        "properties": "Finesse, reach, special"
    },
    {
        "name": "Club shield",
        "damage": "1d4 bludgeoning",
        "weight": "2 lb.",
        "cost": "25 gp",
        "properties": "Light, special"
    },
    {
        "name": "Khopesh",
        "damage": "1d6 slashing",
        "weight": "4 lb.",
        "cost": "25 gp",
        "properties": "Special, versatile (1d8)"
    },
    {
        "name": "Narumbeki throwing knife",
        "damage": "1d6 piercing",
        "weight": "2 lb.",
        "cost": "20 gp",
        "properties": "Light, thrown (range 20/60)"
    },
    {
        "name": "Shotel",
        "damage": "1d6 slashing",
        "weight": "3 lb.",
        "cost": "50 gp",
        "properties": "Finesse, special"
    },
    {
        "name": "Stabbing axe",
        "damage": "1d6 slashing",
        "weight": "4 lb.",
        "cost": "20 gp",
        "properties": "Special, versatile (1d8)"
    },
    {
        "name": "Temple sword",
        "damage": "1d6 slashing",
        "weight": "3 lb.",
        "cost": "35 gp",
        "properties": "Finesse, light"
    },
    {
        "name": "Wrist knife",
        "damage": "1d4 slashing",
        "weight": "1 lb.",
        "cost": "4 gp",
        "properties": "Finesse, light"
    },
]

# Martial Ranged Weapons
MARTIAL_RANGED_WEAPONS = [
    {
        "name": "Double blowgun",
        "damage": "1 piercing",
        "weight": "2 lb.",
        "cost": "40 gp",
        "properties": "Ammunition (range 20/60), loading"
    },
    {
        "name": "War boomerang",
        "damage": "1d6 bludgeoning",
        "weight": "1 lb.",
        "cost": "2 gp",
        "properties": "Finesse, thrown (range 20/60)"
    },
]

# Special weapon property descriptions
SPECIAL_WEAPON_PROPERTIES = [
    {
        "name": "Special (Bladed Scarf)",
        "desc": "If you use one of your attacks to grapple a creature while wielding a bladed scarf, you can use your bonus action to make an attack against it with one end of the scarf. If you use your action to Attack with your scarf, you can use your bonus action to make an attack with the other end of it, dealing 1d4 slashing damage on a hit."
    },
    {
        "name": "Special (Club Shield)",
        "desc": "These shields are wielded by grasping onto a stout two-foot-long pole on the reverse side, allowing you to use your shield as an effective weapon. Wielding a club shield increases your Armor Class by 2. You can't wield a shield or a second club shield at the same time."
    },
    {
        "name": "Special (Double Blowgun)",
        "desc": "The double blowgun is a ranged martial weapon comprised of two hollow tubes connected to one mouthpiece. When a proficient wielder uses an Attack action to blow into it and each tube is loaded with a needle, the wielder can attack two targets within range that are within 5 feet of each other."
    },
    {
        "name": "Special (Khopesh)",
        "desc": "A khopesh is a one-handed martial melee weapon that looks like a cross between a sword and a sickle. The long blade emerges from the hilt straight like a longsword, but the blade curves toward the end. The curve of the blade can be used to trap an opponent's limb. In place of an attack against a humanoid, you can attempt to grapple it with an attack roll. On a hit, the target is grappled. The escape DC is your Strength (Athletics) check. When a creature you have grappled with this weapon attempts to escape and fails, it takes 1d4 + your Strength modifier slashing damage."
    },
    {
        "name": "Special (Shotel)",
        "desc": "The curve of a shotel's blade allows you to reach around your opponent's shield. When you attack a creature wielding a shield, you gain a +2 bonus to the attack roll."
    },
    {
        "name": "Special (Stabbing Axe)",
        "desc": "The long head of this axe is sharply pointed at the top curve, allowing you to use it as a short-hafted spear. You can choose to deal piercing damage instead of the listed slashing damage."
    },
    {
        "name": "Special (War Boomerang)",
        "desc": "A war boomerang is a martial ranged weapon. It is a flat, curved piece of wood with more heft than its smaller cousin. While it does more damage than a regular boomerang, it doesn't return to its wielder on a miss. The boomerang can be used to knock a target unconscious rather than kill it when thrown by a proficient wielder."
    },
]

# Adventuring Gear
ADVENTURING_GEAR = [
    {
        "name": "Camel saddle",
        "desc": "Camels are the most common mounts available in the Southlands, as they are ideal for traveling through the desert. A properly fitted camel saddle allows you to ride on your mount's humped back in comfort.",
        "cost": "60 gp",
        "weight": "40 lb.",
        "category": "adventuring-gear"
    },
    {
        "name": "Elephant saddle",
        "desc": "Elephants make for fearsome beasts of war but can be uncomfortable to ride for extended periods. An elephant saddle resembles a wide-seated chair with a low back and armrests.",
        "cost": "150 gp",
        "weight": "90 lb.",
        "category": "adventuring-gear"
    },
    {
        "name": "Ritual cymbals",
        "desc": "These small brass cymbals are worn on the fingers and struck together as part of ritual dances.",
        "cost": "2 gp",
        "weight": "0 lb.",
        "category": "adventuring-gear"
    },
    {
        "name": "Sand skimmer",
        "desc": "This wooden land vehicle slides atop sand, propelled by a single sail. The skimmer sits atop two narrow runners attached to a flat wooden platform. The platform is five feet wide and ten feet long. One driver pilots the skimmer; it can also hold one passenger. Depending on the wind, the sand skimmer reaches speeds up to 8 miles per hour.",
        "cost": "50 gp",
        "weight": "50 lb.",
        "category": "land-vehicle"
    },
    {
        "name": "Shroud strips",
        "desc": "Shroud strips are alchemically treated strips of cloth or leather used to wrap a corpse. When the body is completely wrapped in shroud strips, it ceases to decay and can't become undead. The first month a body is wrapped in these strips doesn't count against the time limit of spells such as raise dead. Some clerics of life or sun deities create enchanted shroud strips that prevent bodies from being turned into undead creatures.",
        "cost": "75 gp",
        "weight": "1 lb.",
        "category": "adventuring-gear"
    },
    {
        "name": "Silt mask",
        "desc": "This covering keeps sand and other irritants out of the respiratory tract. Creatures wearing a silt mask have advantage on saving throws against effects that are delivered through breathing. Casting a spell with verbal components while wearing a silt mask requires a DC 10 Constitution check; on a failure, the spell slot is expended without effect.",
        "cost": "5 gp",
        "weight": "0.5 lb.",
        "category": "adventuring-gear"
    },
    {
        "name": "Surgery kit",
        "desc": "This leather roll-up can be fastened with an attached cord for storage. It contains several sharp scalpels, a whetstone, a small mirror, sponges, bandages, several needles, a small box of soap, and a bobbin of strong silk thread. In addition to its use as a common medical kit, if you treat an injured creature with a surgical kit during a short rest and the creature uses a Hit Die to recover hit points, it can treat any 1 or 2 it rolls as a 3 instead. The kit has enough consumable material for 10 uses. The consumable portion can be replaced for 5 gp per expended use.",
        "cost": "50 gp",
        "weight": "4 lb.",
        "category": "adventuring-gear"
    },
]


def convert_weapons() -> list:
    """Convert all weapons to Open5e format."""
    weapons = []

    # Process simple melee weapons
    for wpn in SIMPLE_MELEE_WEAPONS:
        damage_dice, damage_type = parse_damage(wpn["damage"])
        short_range, long_range = parse_range(wpn["properties"])

        weapons.append({
            "model": "api_v2.weapon",
            "pk": f"{DOC_KEY}_{slugify(wpn['name'])}",
            "fields": {
                "name": wpn["name"],
                "document": DOC_KEY,
                "damage_dice": damage_dice,
                "damage_type": damage_type,
                "is_simple": True,
                "is_improvised": False,
                "range": short_range,
                "long_range": long_range,
                "distance_unit": None
            }
        })

    # Process martial melee weapons
    for wpn in MARTIAL_MELEE_WEAPONS:
        damage_dice, damage_type = parse_damage(wpn["damage"])
        short_range, long_range = parse_range(wpn["properties"])

        weapons.append({
            "model": "api_v2.weapon",
            "pk": f"{DOC_KEY}_{slugify(wpn['name'])}",
            "fields": {
                "name": wpn["name"],
                "document": DOC_KEY,
                "damage_dice": damage_dice,
                "damage_type": damage_type,
                "is_simple": False,
                "is_improvised": False,
                "range": short_range,
                "long_range": long_range,
                "distance_unit": None
            }
        })

    # Process martial ranged weapons
    for wpn in MARTIAL_RANGED_WEAPONS:
        damage_dice, damage_type = parse_damage(wpn["damage"])
        short_range, long_range = parse_range(wpn["properties"])

        weapons.append({
            "model": "api_v2.weapon",
            "pk": f"{DOC_KEY}_{slugify(wpn['name'])}",
            "fields": {
                "name": wpn["name"],
                "document": DOC_KEY,
                "damage_dice": damage_dice,
                "damage_type": damage_type,
                "is_simple": False,
                "is_improvised": False,
                "range": short_range,
                "long_range": long_range,
                "distance_unit": None
            }
        })

    return weapons


def convert_weapon_properties() -> list:
    """Convert special weapon properties to Open5e format."""
    properties = []

    for prop in SPECIAL_WEAPON_PROPERTIES:
        properties.append({
            "model": "api_v2.weaponproperty",
            "pk": f"{DOC_KEY}_{slugify(prop['name'])}-wp",
            "fields": {
                "name": prop["name"],
                "desc": prop["desc"],
                "document": DOC_KEY,
                "type": None
            }
        })

    return properties


def parse_cost(cost_str: str) -> str:
    """Parse cost string to decimal format."""
    match = re.match(r"(\d+)\s*gp", cost_str)
    if match:
        return f"{match.group(1)}.00"
    return "0.00"


def parse_weight(weight_str: str) -> str:
    """Parse weight string to decimal format."""
    match = re.match(r"([\d.]+)\s*lb", weight_str)
    if match:
        return f"{float(match.group(1)):.3f}"
    return "0.000"


def convert_items() -> list:
    """Convert adventuring gear to Open5e format."""
    items = []

    for item in ADVENTURING_GEAR:
        items.append({
            "model": "api_v2.item",
            "pk": f"{DOC_KEY}_{slugify(item['name'])}",
            "fields": {
                "name": item["name"],
                "desc": item["desc"],
                "document": DOC_KEY,
                "category": item["category"],
                "cost": parse_cost(item["cost"]),
                "weight": parse_weight(item["weight"]),
                "rarity": "common",
                "requires_attunement": False,
                "size": "tiny",
                "armor": None,
                "weapon": None,
                "armor_class": 0,
                "armor_detail": "",
                "hit_points": 0,
                "hit_dice": None,
                "damage_immunities": [],
                "damage_resistances": [],
                "damage_vulnerabilities": [],
                "nonmagical_attack_immunity": False,
                "nonmagical_attack_resistance": False
            }
        })

    return items


def main():
    print("=" * 60)
    print("Southlands Player's Guide Equipment Converter")
    print("=" * 60)

    # Convert weapons
    weapons = convert_weapons()
    print(f"\nConverted {len(weapons)} weapons")

    wpn_path = DATA_V2_DIR / "Weapon.json"
    with open(wpn_path, "w", encoding="utf-8") as f:
        json.dump(weapons, f, indent=2, ensure_ascii=False)
    print(f"Saved weapons to {wpn_path}")

    # Convert weapon properties
    properties = convert_weapon_properties()
    print(f"\nConverted {len(properties)} weapon properties")

    prop_path = DATA_V2_DIR / "WeaponProperty.json"
    with open(prop_path, "w", encoding="utf-8") as f:
        json.dump(properties, f, indent=2, ensure_ascii=False)
    print(f"Saved weapon properties to {prop_path}")

    # Convert items
    items = convert_items()
    print(f"\nConverted {len(items)} items")

    item_path = DATA_V2_DIR / "Item.json"
    with open(item_path, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
    print(f"Saved items to {item_path}")

    print("\n" + "=" * 60)
    print("Conversion complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
