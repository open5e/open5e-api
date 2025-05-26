#!/usr/bin/env python3
"""
SRD 5.2 Equipment Converter

This script converts equipment (weapons, armor, and items) from the D&D SRD 5.2 markdown format 
to Open5e API v2 JSON format, creating separate files for Weapon, Armor, WeaponProperty, 
and WeaponPropertyAssignment data.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

def clean_text(text: str) -> str:
    """Clean text by removing markdown formatting and extra whitespace."""
    if not text:
        return ""
    
    # Remove markdown formatting
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
    text = re.sub(r'\*(.*?)\*', r'\1', text)      # Italic
    text = re.sub(r'`(.*?)`', r'\1', text)        # Code
    
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def create_weapon_pk(name: str) -> str:
    """Create primary key for weapon."""
    # Convert to lowercase, replace spaces with hyphens, remove special chars
    pk = re.sub(r'[^\w\s-]', '', name.lower())
    pk = re.sub(r'[-\s]+', '-', pk)
    return f"srd2024_{pk}"

def create_armor_pk(name: str) -> str:
    """Create primary key for armor."""
    # Convert to lowercase, replace spaces with hyphens, remove special chars
    pk = re.sub(r'[^\w\s-]', '', name.lower())
    pk = re.sub(r'[-\s]+', '-', pk)
    return f"srd2024_{pk}"

def parse_damage_dice(damage_str: str) -> str:
    """Parse damage dice from string like '1d4 Bludgeoning' -> '1d4'."""
    match = re.search(r'(\d+d\d+|\d+)', damage_str)
    return match.group(1) if match else "1d4"

def parse_damage_type(damage_str: str) -> str:
    """Parse damage type from string like '1d4 Bludgeoning' -> 'bludgeoning'."""
    damage_types = ['bludgeoning', 'piercing', 'slashing', 'acid', 'cold', 'fire', 'force', 
                   'lightning', 'necrotic', 'poison', 'psychic', 'radiant', 'thunder']
    
    damage_str_lower = damage_str.lower()
    for dtype in damage_types:
        if dtype in damage_str_lower:
            return dtype
    
    return "bludgeoning"  # default

def parse_range(properties_str: str) -> Tuple[float, float]:
    """Parse range from properties string."""
    # Look for patterns like "Range 20/60" or "Thrown (Range 20/60)"
    range_match = re.search(r'Range\s+(\d+)/(\d+)', properties_str)
    if range_match:
        return float(range_match.group(1)), float(range_match.group(2))
    
    # Look for thrown weapons
    thrown_match = re.search(r'Thrown\s*\(Range\s+(\d+)/(\d+)\)', properties_str)
    if thrown_match:
        return float(thrown_match.group(1)), float(thrown_match.group(2))
    
    return 0.0, 0.0

def parse_weapon_properties(properties_str: str) -> List[str]:
    """Parse weapon properties from properties string."""
    properties = []
    
    # Standard properties
    if 'ammunition' in properties_str.lower():
        properties.append('ammunition')
    if 'finesse' in properties_str.lower():
        properties.append('finesse')
    if 'heavy' in properties_str.lower():
        properties.append('heavy')
    if 'light' in properties_str.lower():
        properties.append('light')
    if 'loading' in properties_str.lower():
        properties.append('loading')
    if 'reach' in properties_str.lower():
        properties.append('reach')
    if 'thrown' in properties_str.lower():
        properties.append('thrown')
    if 'two-handed' in properties_str.lower():
        properties.append('two-handed')
    if 'versatile' in properties_str.lower():
        properties.append('versatile')
    
    return properties

def get_versatile_damage(properties_str: str) -> Optional[str]:
    """Extract versatile damage from properties string."""
    versatile_match = re.search(r'Versatile\s*\(([^)]+)\)', properties_str)
    if versatile_match:
        return versatile_match.group(1)
    return None

def parse_weapons_table(table_text: str, is_simple: bool) -> List[Dict[str, Any]]:
    """Parse a weapons table and return weapon data."""
    weapons = []
    
    # Split into lines and find table rows
    lines = table_text.strip().split('\n')
    
    for line in lines:
        if '|' in line and not line.startswith('|---'):
            parts = [p.strip() for p in line.split('|') if p.strip()]
            
            if len(parts) >= 6:  # Name, Damage, Properties, Mastery, Weight, Cost
                try:
                    name = clean_text(parts[0])
                    damage = clean_text(parts[1])
                    properties = clean_text(parts[2])
                    mastery = clean_text(parts[3])
                    weight = clean_text(parts[4])
                    cost = clean_text(parts[5])
                    
                    if name and name != 'Name':  # Skip header row
                        weapon_pk = create_weapon_pk(name)
                        
                        # Parse damage
                        damage_dice = parse_damage_dice(damage)
                        damage_type = parse_damage_type(damage)
                        
                        # Parse range
                        range_normal, range_long = parse_range(properties)
                        
                        weapon_data = {
                            "model": "api_v2.weapon",
                            "pk": weapon_pk,
                            "fields": {
                                "name": name,
                                "document": "srd-2024",
                                "damage_type": damage_type,
                                "damage_dice": damage_dice,
                                "range": range_normal,
                                "long_range": range_long,
                                "distance_unit": None,
                                "is_simple": is_simple,
                                "is_improvised": False
                            }
                        }
                        
                        weapons.append({
                            'weapon': weapon_data,
                            'properties': properties,
                            'mastery': mastery,
                            'name': name
                        })
                        
                except (IndexError, ValueError) as e:
                    print(f"Error parsing weapon line: {line} - {e}")
                    continue
    
    return weapons

def parse_armor_table(table_text: str) -> List[Dict[str, Any]]:
    """Parse an armor table and return armor data."""
    armors = []
    
    # Split into lines and find table rows
    lines = table_text.strip().split('\n')
    
    for line in lines:
        if '|' in line and not line.startswith('|---'):
            parts = [p.strip() for p in line.split('|') if p.strip()]
            
            if len(parts) >= 6:  # Armor, AC, Strength, Stealth, Weight, Cost
                try:
                    name = clean_text(parts[0])
                    ac_str = clean_text(parts[1])
                    strength_str = clean_text(parts[2])
                    stealth_str = clean_text(parts[3])
                    weight = clean_text(parts[4])
                    cost = clean_text(parts[5])
                    
                    if name and name != 'Armor' and 'Don or Doff' not in name:  # Skip headers
                        armor_pk = create_armor_pk(name)
                        
                        # Parse AC
                        ac_base = 10
                        ac_add_dexmod = False
                        ac_cap_dexmod = None
                        
                        if 'Dex modifier' in ac_str:
                            ac_add_dexmod = True
                            # Extract base AC
                            ac_match = re.search(r'(\d+)', ac_str)
                            if ac_match:
                                ac_base = int(ac_match.group(1))
                            
                            # Check for cap
                            if 'max 2' in ac_str:
                                ac_cap_dexmod = 2
                        else:
                            # Fixed AC
                            ac_match = re.search(r'(\d+)', ac_str)
                            if ac_match:
                                ac_base = int(ac_match.group(1))
                        
                        # Parse strength requirement
                        strength_required = None
                        if strength_str and strength_str != '—':
                            str_match = re.search(r'(\d+)', strength_str)
                            if str_match:
                                strength_required = int(str_match.group(1))
                        
                        # Parse stealth disadvantage
                        stealth_disadvantage = 'Disadvantage' in stealth_str
                        
                        armor_data = {
                            "model": "api_v2.armor",
                            "pk": armor_pk,
                            "fields": {
                                "name": name,
                                "document": "srd-2024",
                                "grants_stealth_disadvantage": stealth_disadvantage,
                                "strength_score_required": strength_required,
                                "ac_base": ac_base,
                                "ac_add_dexmod": ac_add_dexmod,
                                "ac_cap_dexmod": ac_cap_dexmod
                            }
                        }
                        
                        armors.append(armor_data)
                        
                except (IndexError, ValueError) as e:
                    print(f"Error parsing armor line: {line} - {e}")
                    continue
    
    return armors

def create_mastery_properties() -> List[Dict[str, Any]]:
    """Create the new weapon mastery properties for SRD 2024."""
    mastery_properties = [
        {
            "model": "api_v2.weaponproperty",
            "pk": "srd-2024_cleave-mastery",
            "fields": {
                "name": "Cleave",
                "document": "srd-2024",
                "type": "Mastery",
                "desc": "If you hit a creature with a melee attack roll using this weapon, you can make a melee attack roll with the weapon against a second creature within 5 feet of the first that is also within your reach. On a hit, the second creature takes the weapon's damage, but don't add your ability modifier to that damage unless that modifier is negative. You can make this extra attack only once per turn."
            }
        },
        {
            "model": "api_v2.weaponproperty",
            "pk": "srd-2024_graze-mastery",
            "fields": {
                "name": "Graze",
                "document": "srd-2024",
                "type": "Mastery",
                "desc": "If your attack roll with this weapon misses a creature, you can deal damage to that creature equal to the ability modifier you used to make the attack roll. This damage is the same type dealt by the weapon, and the damage can be increased only by increasing the ability modifier."
            }
        },
        {
            "model": "api_v2.weaponproperty",
            "pk": "srd-2024_nick-mastery",
            "fields": {
                "name": "Nick",
                "document": "srd-2024",
                "type": "Mastery",
                "desc": "When you make the extra attack of the Light property, you can make it as part of the Attack action instead of as a Bonus Action. You can make this extra attack only once per turn."
            }
        },
        {
            "model": "api_v2.weaponproperty",
            "pk": "srd-2024_push-mastery",
            "fields": {
                "name": "Push",
                "document": "srd-2024",
                "type": "Mastery",
                "desc": "If you hit a creature with this weapon, you can push the creature up to 10 feet straight away from yourself if it is Large or smaller."
            }
        },
        {
            "model": "api_v2.weaponproperty",
            "pk": "srd-2024_sap-mastery",
            "fields": {
                "name": "Sap",
                "document": "srd-2024",
                "type": "Mastery",
                "desc": "If you hit a creature with this weapon, that creature has Disadvantage on its next attack roll before the start of your next turn."
            }
        },
        {
            "model": "api_v2.weaponproperty",
            "pk": "srd-2024_slow-mastery",
            "fields": {
                "name": "Slow",
                "document": "srd-2024",
                "type": "Mastery",
                "desc": "If you hit a creature with this weapon and deal damage to it, you can reduce its Speed by 10 feet until the start of your next turn. If the creature is hit more than once by weapons that have this property, the Speed reduction doesn't exceed 10 feet."
            }
        },
        {
            "model": "api_v2.weaponproperty",
            "pk": "srd-2024_topple-mastery",
            "fields": {
                "name": "Topple",
                "document": "srd-2024",
                "type": "Mastery",
                "desc": "If you hit a creature with this weapon, you can force the creature to make a Constitution saving throw (DC 8 plus the ability modifier used to make the attack roll and your Proficiency Bonus). On a failed save, the creature has the Prone condition."
            }
        },
        {
            "model": "api_v2.weaponproperty",
            "pk": "srd-2024_vex-mastery",
            "fields": {
                "name": "Vex",
                "document": "srd-2024",
                "type": "Mastery",
                "desc": "If you hit a creature with this weapon and deal damage to the creature, you have Advantage on your next attack roll against that creature before the end of your next turn."
            }
        }
    ]
    
    return mastery_properties

def create_standard_properties() -> List[Dict[str, Any]]:
    """Create the standard weapon properties for SRD 2024 (updated descriptions)."""
    standard_properties = [
        {
            "model": "api_v2.weaponproperty",
            "pk": "srd-2024_ammunition-wp",
            "fields": {
                "name": "Ammunition",
                "document": "srd-2024",
                "desc": "You can use a weapon that has the Ammunition property to make a ranged attack only if you have ammunition to fire from it. The type of ammunition required is specified with the weapon's range. Each attack expends one piece of ammunition. Drawing the ammunition is part of the attack (you need a free hand to load a one-handed weapon). After a fight, you can spend 1 minute to recover half the ammunition (round down) you used in the fight; the rest is lost."
            }
        },
        {
            "model": "api_v2.weaponproperty",
            "pk": "srd-2024_finesse-wp",
            "fields": {
                "name": "Finesse",
                "document": "srd-2024",
                "desc": "When making an attack with a Finesse weapon, use your choice of your Strength or Dexterity modifier for the attack and damage rolls. You must use the same modifier for both rolls."
            }
        },
        {
            "model": "api_v2.weaponproperty",
            "pk": "srd-2024_heavy-wp",
            "fields": {
                "name": "Heavy",
                "document": "srd-2024",
                "desc": "You have Disadvantage on attack rolls with a Heavy weapon if it's a Melee weapon and your Strength score isn't at least 13 or if it's a Ranged weapon and your Dexterity score isn't at least 13."
            }
        },
        {
            "model": "api_v2.weaponproperty",
            "pk": "srd-2024_light-wp",
            "fields": {
                "name": "Light",
                "document": "srd-2024",
                "desc": "When you take the Attack action on your turn and attack with a Light weapon, you can make one extra attack as a Bonus Action later on the same turn. That extra attack must be made with a different Light weapon, and you don't add your ability modifier to the extra attack's damage unless that modifier is negative."
            }
        },
        {
            "model": "api_v2.weaponproperty",
            "pk": "srd-2024_loading-wp",
            "fields": {
                "name": "Loading",
                "document": "srd-2024",
                "desc": "You can fire only one piece of ammunition from a Loading weapon when you use an action, a Bonus Action, or a Reaction to fire it, regardless of the number of attacks you can normally make."
            }
        },
        {
            "model": "api_v2.weaponproperty",
            "pk": "srd-2024_range-wp",
            "fields": {
                "name": "Range",
                "document": "srd-2024",
                "desc": "A Range weapon has a range in parentheses after the Ammunition or Thrown property. The range lists two numbers. The first is the weapon's normal range in feet, and the second is the weapon's long range. When attacking a target beyond normal range, you have Disadvantage on the attack roll. You can't attack a target beyond the long range."
            }
        },
        {
            "model": "api_v2.weaponproperty",
            "pk": "srd-2024_reach-wp",
            "fields": {
                "name": "Reach",
                "document": "srd-2024",
                "desc": "A Reach weapon adds 5 feet to your reach when you attack with it, as well as when determining your reach for Opportunity Attacks with it."
            }
        },
        {
            "model": "api_v2.weaponproperty",
            "pk": "srd-2024_thrown-wp",
            "fields": {
                "name": "Thrown",
                "document": "srd-2024",
                "desc": "If a weapon has the Thrown property, you can throw the weapon to make a ranged attack, and you can draw that weapon as part of the attack. If the weapon is a Melee weapon, use the same ability modifier for the attack and damage rolls that you use for a melee attack with that weapon."
            }
        },
        {
            "model": "api_v2.weaponproperty",
            "pk": "srd-2024_two-handed-wp",
            "fields": {
                "name": "Two-Handed",
                "document": "srd-2024",
                "desc": "A Two-Handed weapon requires two hands when you attack with it."
            }
        },
        {
            "model": "api_v2.weaponproperty",
            "pk": "srd-2024_versatile-wp",
            "fields": {
                "name": "Versatile",
                "document": "srd-2024",
                "desc": "A Versatile weapon can be used with one or two hands. A damage value in parentheses appears with the property. The weapon deals that damage when used with two hands to make a melee attack."
            }
        }
    ]
    
    return standard_properties

def create_property_assignments(weapons_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Create weapon property assignments for all weapons."""
    assignments = []
    
    for weapon_info in weapons_data:
        weapon = weapon_info['weapon']
        properties_str = weapon_info['properties']
        mastery = weapon_info['mastery']
        weapon_pk = weapon['pk']
        
        # Standard properties
        standard_props = parse_weapon_properties(properties_str)
        
        for prop in standard_props:
            assignment_pk = f"srd-2024_{weapon_pk.replace('srd2024_', '')}_{prop}"
            
            assignment = {
                "model": "api_v2.weaponpropertyassignment",
                "pk": assignment_pk,
                "fields": {
                    "weapon": weapon_pk,
                    "property": f"srd-2024_{prop}-wp",
                    "document": "srd-2024"
                }
            }
            
            # Add detail for versatile weapons
            if prop == 'versatile':
                versatile_damage = get_versatile_damage(properties_str)
                if versatile_damage:
                    assignment["fields"]["detail"] = versatile_damage
            
            assignments.append(assignment)
        
        # Mastery property
        if mastery and mastery != '—':
            mastery_lower = mastery.lower()
            mastery_pk = f"srd-2024_{weapon_pk.replace('srd2024_', '')}_{mastery_lower}-mastery"
            
            mastery_assignment = {
                "model": "api_v2.weaponpropertyassignment",
                "pk": mastery_pk,
                "fields": {
                    "weapon": weapon_pk,
                    "property": f"srd-2024_{mastery_lower}-mastery",
                    "document": "srd-2024"
                }
            }
            
            assignments.append(mastery_assignment)
    
    return assignments

def main():
    """Main function to convert equipment."""
    input_file = Path("../sections/07_equipment.md")
    output_dir = Path("../../../v2/wizards-of-the-coast/srd-2024/")
    
    if not input_file.exists():
        print(f"Error: Input file {input_file} not found")
        return
    
    # Read the input file
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("Converting equipment...")
    
    # Extract weapon tables
    simple_melee_match = re.search(r'Table: Simple Melee Weapons\s*\n(.*?)(?=Table:|$)', content, re.DOTALL)
    simple_ranged_match = re.search(r'Table: Simple Ranged Weapons\s*\n(.*?)(?=Table:|$)', content, re.DOTALL)
    martial_melee_match = re.search(r'Table: Martial Melee Weapons\s*\n(.*?)(?=Table:|$)', content, re.DOTALL)
    martial_ranged_match = re.search(r'Table: Martial Ranged Weapons\s*\n(.*?)(?=Table:|$)', content, re.DOTALL)
    
    # Extract armor tables
    light_armor_match = re.search(r'Table: Light Armor.*?\n(.*?)(?=Table:|$)', content, re.DOTALL)
    medium_armor_match = re.search(r'Table: Medium Armor.*?\n(.*?)(?=Table:|$)', content, re.DOTALL)
    heavy_armor_match = re.search(r'Table: Heavy Armor.*?\n(.*?)(?=Table:|$)', content, re.DOTALL)
    shield_match = re.search(r'Table: Shield.*?\n(.*?)(?=Table:|$)', content, re.DOTALL)
    
    # Parse weapons
    all_weapons_data = []
    
    if simple_melee_match:
        simple_melee = parse_weapons_table(simple_melee_match.group(1), True)
        all_weapons_data.extend(simple_melee)
        print(f"Parsed {len(simple_melee)} simple melee weapons")
    
    if simple_ranged_match:
        simple_ranged = parse_weapons_table(simple_ranged_match.group(1), True)
        all_weapons_data.extend(simple_ranged)
        print(f"Parsed {len(simple_ranged)} simple ranged weapons")
    
    if martial_melee_match:
        martial_melee = parse_weapons_table(martial_melee_match.group(1), False)
        all_weapons_data.extend(martial_melee)
        print(f"Parsed {len(martial_melee)} martial melee weapons")
    
    if martial_ranged_match:
        martial_ranged = parse_weapons_table(martial_ranged_match.group(1), False)
        all_weapons_data.extend(martial_ranged)
        print(f"Parsed {len(martial_ranged)} martial ranged weapons")
    
    # Parse armor
    all_armor = []
    
    if light_armor_match:
        light_armor = parse_armor_table(light_armor_match.group(1))
        all_armor.extend(light_armor)
        print(f"Parsed {len(light_armor)} light armor pieces")
    
    if medium_armor_match:
        medium_armor = parse_armor_table(medium_armor_match.group(1))
        all_armor.extend(medium_armor)
        print(f"Parsed {len(medium_armor)} medium armor pieces")
    
    if heavy_armor_match:
        heavy_armor = parse_armor_table(heavy_armor_match.group(1))
        all_armor.extend(heavy_armor)
        print(f"Parsed {len(heavy_armor)} heavy armor pieces")
    
    if shield_match:
        shields = parse_armor_table(shield_match.group(1))
        all_armor.extend(shields)
        print(f"Parsed {len(shields)} shields")
    
    # Create properties and assignments
    mastery_properties = create_mastery_properties()
    standard_properties = create_standard_properties()
    all_properties = mastery_properties + standard_properties
    
    property_assignments = create_property_assignments(all_weapons_data)
    
    # Extract just the weapon objects
    weapons = [w['weapon'] for w in all_weapons_data]
    
    # Write output files
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write weapons
    weapons_file = output_dir / "Weapon.json"
    with open(weapons_file, 'w', encoding='utf-8') as f:
        json.dump(weapons, f, indent=2, ensure_ascii=False)
    
    # Write armor
    armor_file = output_dir / "Armor.json"
    with open(armor_file, 'w', encoding='utf-8') as f:
        json.dump(all_armor, f, indent=2, ensure_ascii=False)
    
    # Write weapon properties
    properties_file = output_dir / "WeaponProperty.json"
    with open(properties_file, 'w', encoding='utf-8') as f:
        json.dump(all_properties, f, indent=2, ensure_ascii=False)
    
    # Write property assignments
    assignments_file = output_dir / "WeaponPropertyAssignment.json"
    with open(assignments_file, 'w', encoding='utf-8') as f:
        json.dump(property_assignments, f, indent=2, ensure_ascii=False)
    
    print(f"\nConversion completed!")
    print(f"Converted {len(weapons)} weapons")
    print(f"Converted {len(all_armor)} armor pieces")
    print(f"Created {len(all_properties)} weapon properties ({len(mastery_properties)} mastery + {len(standard_properties)} standard)")
    print(f"Generated {len(property_assignments)} property assignments")
    print(f"Files written to {output_dir}")

if __name__ == "__main__":
    main() 