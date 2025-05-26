#!/usr/bin/env python3
"""
SRD 5.2 Enhanced Equipment Converter

This script converts equipment from the D&D SRD 5.2 standardized markdown format 
to Open5e API v2 JSON format, creating separate files for:
- Weapon.json
- Armor.json  
- WeaponProperty.json
- WeaponPropertyAssignment.json
- Item.json (for adventuring gear, tools, mounts, vehicles, services, magic items)
- ItemCategory.json
- ItemSet.json
- Rule.json (for weapon rules)
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

def create_pk(name: str, prefix: str = "srd2024") -> str:
    """Create primary key from name."""
    # Remove cost information from name (e.g., "Cook's Utensils (1 GP)" -> "Cook's Utensils")
    clean_name = re.sub(r'\s*\([^)]*[Gg][Pp]\)', '', name)
    clean_name = re.sub(r'\s*\([^)]*[Ss][Pp]\)', '', clean_name)
    clean_name = re.sub(r'\s*\([^)]*[Cc][Pp]\)', '', clean_name)
    
    # Convert to lowercase, replace spaces with hyphens, remove special chars
    pk = re.sub(r'[^\w\s-]', '', clean_name.lower())
    pk = re.sub(r'[-\s]+', '-', pk)
    return f"{prefix}_{pk}"

def parse_cost(cost_str: str) -> str:
    """Parse cost string and convert to decimal format."""
    if not cost_str or cost_str == "—":
        return "0.00"
    
    # Handle different formats
    cost_str = cost_str.upper().replace(',', '')
    
    if 'GP' in cost_str:
        amount = re.search(r'(\d+(?:\.\d+)?)', cost_str)
        if amount:
            return f"{float(amount.group(1)):.2f}"
    elif 'SP' in cost_str:
        amount = re.search(r'(\d+(?:\.\d+)?)', cost_str)
        if amount:
            return f"{float(amount.group(1)) * 0.1:.2f}"
    elif 'CP' in cost_str:
        amount = re.search(r'(\d+(?:\.\d+)?)', cost_str)
        if amount:
            return f"{float(amount.group(1)) * 0.01:.2f}"
    
    return "0.00"

def parse_weight(weight_str: str) -> str:
    """Parse weight string."""
    if not weight_str or weight_str == "—":
        return "0.000"
    
    # Extract numeric value
    weight_match = re.search(r'(\d+(?:\.\d+)?|\d+/\d+)', weight_str)
    if weight_match:
        weight_val = weight_match.group(1)
        if '/' in weight_val:
            # Handle fractions like "1/4"
            parts = weight_val.split('/')
            return f"{float(parts[0]) / float(parts[1]):.3f}"
        return f"{float(weight_val):.3f}"
    
    return "0.000"

def parse_standardized_item(content: str) -> Dict[str, Any]:
    """Parse a standardized item format from markdown."""
    lines = content.strip().split('\n')
    item_data = {}
    
    # Extract name from header
    for line in lines:
        if line.startswith('## '):
            item_data['name'] = line[3:].strip()
            break
    
    # Extract properties - the format is **Key:** Value
    for line in lines:
        if line.startswith('**') and ':**' in line:
            parts = line.split(':**')
            if len(parts) == 2:
                key = parts[0][2:].strip()  # Remove ** from beginning
                value = parts[1].strip()
                item_data[key] = value
    
    return item_data

def parse_magic_item_type_and_rarity(type_line: str) -> Tuple[str, str, bool]:
    """Parse the magic item type and rarity line."""
    # Remove italic markers
    type_line = type_line.strip('*').strip()
    
    # Extract rarity and attunement requirement
    rarity = None
    requires_attunement = False
    category = "wondrous-item"  # default
    
    # Common rarity patterns
    rarity_patterns = [
        r'\b(Artifact)\b',
        r'\b(Legendary)\b', 
        r'\b(Very Rare)\b',
        r'\b(Rare)\b',
        r'\b(Uncommon)\b',
        r'\b(Common)\b'
    ]
    
    for pattern in rarity_patterns:
        match = re.search(pattern, type_line, re.IGNORECASE)
        if match:
            rarity = match.group(1).lower().replace(' ', '-')
            break
    
    # Check for attunement requirement
    if 'requires attunement' in type_line.lower():
        requires_attunement = True
    
    # Determine category from type
    type_lower = type_line.lower()
    if 'armor' in type_lower:
        category = "armor"
    elif 'weapon' in type_lower:
        category = "weapon"
    elif 'shield' in type_lower:
        category = "shield"
    elif 'potion' in type_lower:
        category = "potion"
    elif 'scroll' in type_lower:
        category = "scroll"
    elif 'ring' in type_lower:
        category = "ring"
    elif 'rod' in type_lower:
        category = "rod"
    elif 'staff' in type_lower:
        category = "staff"
    elif 'wand' in type_lower:
        category = "wand"
    else:
        category = "wondrous-item"
    
    return category, rarity, requires_attunement

def convert_magic_items(magic_items_file: Path) -> List[Dict[str, Any]]:
    """Convert magic items from the SRD 5.2 format."""
    if not magic_items_file.exists():
        return []
    
    with open(magic_items_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    magic_items = []
    
    # Split into individual magic item sections
    item_sections = re.split(r'\n### ', content)
    
    for section in item_sections[1:]:  # Skip the header
        lines = section.strip().split('\n')
        if not lines:
            continue
            
        # Extract name from first line
        name = lines[0].strip()
        name = clean_text(name)  # Clean any markdown formatting from name
        if not name:
            continue
        
        # Find the type/rarity line (should be in italics)
        type_line = ""
        desc_start_idx = 1
        
        for i, line in enumerate(lines[1:], 1):
            line = line.strip()
            if line.startswith('*') and line.endswith('*'):
                type_line = line
                desc_start_idx = i + 1
                break
        
        if not type_line:
            continue
        
        # Parse type and rarity
        category, rarity, requires_attunement = parse_magic_item_type_and_rarity(type_line)
        
        # Extract description (everything after the type line)
        desc_lines = []
        for line in lines[desc_start_idx:]:
            line = line.strip()
            if line and not line.startswith('|') and not line.startswith('Table:'):
                desc_lines.append(line)
        
        desc = ' '.join(desc_lines) if desc_lines else f"A magical {name.lower()}."
        desc = clean_text(desc)
        
        # Create primary key
        item_pk = create_pk(name)
        
        # Create magic item
        magic_item = {
            "model": "api_v2.item",
            "pk": item_pk,
            "fields": {
                "name": name,
                "desc": desc,
                "document": "srd-2024",
                "size": "tiny",
                "weight": "0.000",  # Most magic items don't specify weight
                "armor_class": 0,
                "hit_points": 0,
                "hit_dice": None,
                "nonmagical_attack_resistance": False,
                "nonmagical_attack_immunity": False,
                "cost": "0.00",  # Magic items typically don't have standard costs
                "weapon": None,
                "armor": None,
                "category": category,
                "requires_attunement": requires_attunement,
                "rarity": rarity,  # Reference to 2014 rarity
                "damage_vulnerabilities": [],
                "damage_immunities": [],
                "damage_resistances": []
            }
        }
        
        magic_items.append(magic_item)
    
    return magic_items

def convert_weapons(weapons_file: Path) -> Tuple[List[Dict], List[Dict], List[Dict], List[Dict]]:
    """Convert weapons from standardized format."""
    with open(weapons_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    weapons = []
    weapon_items = []
    property_assignments = []
    
    # Split into individual weapon sections
    weapon_sections = re.split(r'\n## ', content)
    
    for section in weapon_sections[1:]:  # Skip the header
        section = '## ' + section
        weapon_data = parse_standardized_item(section)
        
        if 'name' not in weapon_data:
            continue
            
        name = weapon_data['name']
        weapon_pk = create_pk(name)
        
        # Parse damage
        damage_str = weapon_data.get('Damage', '1d4 Bludgeoning')
        damage_parts = damage_str.split()
        damage_dice = damage_parts[0] if damage_parts else '1d4'
        damage_type = damage_parts[1].lower() if len(damage_parts) > 1 else 'bludgeoning'
        
        # Parse category
        category = weapon_data.get('Category', 'Simple Melee')
        is_simple = 'Simple' in category
        
        # Parse range
        range_val = float(weapon_data.get('Range', '0'))
        long_range_val = float(weapon_data.get('Long Range', '0'))
        
        weapon = {
            "model": "api_v2.weapon",
            "pk": weapon_pk,
            "fields": {
                "name": name,
                "document": "srd-2024",
                "damage_type": damage_type,
                "damage_dice": damage_dice,
                "range": range_val,
                "long_range": long_range_val,
                "distance_unit": None,
                "is_simple": is_simple,
                "is_improvised": False
            }
        }
        
        weapons.append(weapon)
        
        # Create corresponding weapon item (following 2014 pattern)
        cost = parse_cost(weapon_data.get('Cost', '0'))
        weight = parse_weight(weapon_data.get('Weight', '0'))
        
        weapon_item = {
            "model": "api_v2.item",
            "pk": weapon_pk,
            "fields": {
                "name": name,
                "desc": f"A {name.lower()}.",
                "document": "srd-2024",
                "size": "tiny",
                "weight": weight,
                "armor_class": 0,
                "hit_points": 0,
                "hit_dice": None,
                "nonmagical_attack_resistance": False,
                "nonmagical_attack_immunity": False,
                "cost": cost,
                "weapon": weapon_pk,
                "armor": None,
                "category": "weapon",
                "requires_attunement": False,
                "rarity": None,
                "damage_vulnerabilities": [],
                "damage_immunities": ["poison", "psychic"],
                "damage_resistances": []
            }
        }
        
        weapon_items.append(weapon_item)
        
        # Create property assignments
        properties_str = weapon_data.get('Properties', '')
        mastery = weapon_data.get('Mastery', '')
        
        # Standard properties
        if 'Light' in properties_str:
            property_assignments.append(create_property_assignment(weapon_pk, 'light-wp'))
        if 'Finesse' in properties_str:
            property_assignments.append(create_property_assignment(weapon_pk, 'finesse-wp'))
        if 'Heavy' in properties_str:
            property_assignments.append(create_property_assignment(weapon_pk, 'heavy-wp'))
        if 'Reach' in properties_str:
            property_assignments.append(create_property_assignment(weapon_pk, 'reach-wp'))
        if 'Thrown' in properties_str:
            property_assignments.append(create_property_assignment(weapon_pk, 'thrown-wp'))
        if 'Two-Handed' in properties_str:
            property_assignments.append(create_property_assignment(weapon_pk, 'two-handed-wp'))
        if 'Loading' in properties_str:
            property_assignments.append(create_property_assignment(weapon_pk, 'loading-wp'))
        if 'Ammunition' in properties_str:
            property_assignments.append(create_property_assignment(weapon_pk, 'ammunition-wp'))
        if 'Versatile' in properties_str:
            versatile_match = re.search(r'Versatile \(([^)]+)\)', properties_str)
            detail = versatile_match.group(1) if versatile_match else None
            property_assignments.append(create_property_assignment(weapon_pk, 'versatile-wp', detail))
        
        # Mastery property
        if mastery and mastery != '—':
            mastery_lower = mastery.lower()
            property_assignments.append(create_property_assignment(weapon_pk, f'{mastery_lower}-mastery'))
    
    # Create weapon properties
    weapon_properties = create_weapon_properties()
    
    return weapons, weapon_items, weapon_properties, property_assignments

def create_property_assignment(weapon_pk: str, property_name: str, detail: str = None) -> Dict[str, Any]:
    """Create a weapon property assignment."""
    assignment_pk = f"srd-2024_{weapon_pk.replace('srd2024_', '')}_{property_name.replace('-wp', '').replace('-mastery', '')}"
    
    assignment = {
        "model": "api_v2.weaponpropertyassignment",
        "pk": assignment_pk,
        "fields": {
            "weapon": weapon_pk,
            "property": f"srd-2024_{property_name}",
            "document": "srd-2024"
        }
    }
    
    if detail:
        assignment["fields"]["detail"] = detail
    
    return assignment

def create_weapon_properties() -> List[Dict[str, Any]]:
    """Create weapon properties for SRD 2024."""
    properties = [
        # Mastery properties
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
        },
        # Standard properties
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
    
    return properties

def convert_armor(armor_file: Path) -> Tuple[List[Dict], List[Dict]]:
    """Convert armor from standardized format."""
    with open(armor_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    armors = []
    armor_items = []
    
    # Split into individual armor sections
    armor_sections = re.split(r'\n## ', content)
    
    for section in armor_sections[1:]:  # Skip the header
        section = '## ' + section
        armor_data = parse_standardized_item(section)
        
        if 'name' not in armor_data:
            continue
            
        name = armor_data['name']
        armor_pk = create_pk(name)
        
        # Parse AC data
        ac_base = int(armor_data.get('AC Base', '10'))
        ac_add_dex = armor_data.get('AC Add Dex', 'false').lower() == 'true'
        ac_cap_dex_str = armor_data.get('AC Cap Dex', 'null')
        ac_cap_dex = int(ac_cap_dex_str) if ac_cap_dex_str != 'null' else None
        
        # Parse strength requirement
        strength_req_str = armor_data.get('Strength Required', 'null')
        strength_required = int(strength_req_str) if strength_req_str != 'null' else None
        
        # Parse stealth disadvantage
        stealth_disadvantage = armor_data.get('Stealth Disadvantage', 'false').lower() == 'true'
        
        armor = {
            "model": "api_v2.armor",
            "pk": armor_pk,
            "fields": {
                "name": name,
                "document": "srd-2024",
                "grants_stealth_disadvantage": stealth_disadvantage,
                "strength_score_required": strength_required,
                "ac_base": ac_base,
                "ac_add_dexmod": ac_add_dex,
                "ac_cap_dexmod": ac_cap_dex
            }
        }
        
        armors.append(armor)
        
        # Create corresponding armor item (following 2014 pattern)
        cost = parse_cost(armor_data.get('Cost', '0'))
        weight = parse_weight(armor_data.get('Weight', '0'))
        
        armor_item = {
            "model": "api_v2.item",
            "pk": armor_pk,
            "fields": {
                "name": name,
                "desc": f"A {name.lower()}.",
                "document": "srd-2024",
                "size": "tiny",
                "weight": weight,
                "armor_class": 0,
                "hit_points": 0,
                "hit_dice": None,
                "nonmagical_attack_resistance": False,
                "nonmagical_attack_immunity": False,
                "cost": cost,
                "weapon": None,
                "armor": armor_pk,
                "category": "armor",
                "requires_attunement": False,
                "rarity": None,
                "damage_vulnerabilities": [],
                "damage_immunities": ["poison", "psychic"],
                "damage_resistances": []
            }
        }
        
        armor_items.append(armor_item)
    
    return armors, armor_items

def convert_items(item_files: List[Path]) -> List[Dict[str, Any]]:
    """Convert various item types from standardized format."""
    items = []
    
    for item_file in item_files:
        with open(item_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split into individual item sections
        item_sections = re.split(r'\n## ', content)
        
        for section in item_sections[1:]:  # Skip the header
            section = '## ' + section
            item_data = parse_standardized_item(section)
            
            if 'name' not in item_data:
                continue
                
            name = item_data['name']
            item_pk = create_pk(name)
            
            # Parse cost and weight
            cost = parse_cost(item_data.get('Cost', '0'))
            weight = parse_weight(item_data.get('Weight', '0'))
            
            # Get category from the standardized format
            category = item_data.get('Category', 'adventuring-gear')
            
            # Create description from available data
            desc_parts = []
            if 'Description' in item_data:
                desc_parts.append(item_data['Description'])
            if 'Ability' in item_data:
                desc_parts.append(f"Ability: {item_data['Ability']}")
            if 'Utilize' in item_data:
                desc_parts.append(f"Utilize: {item_data['Utilize']}")
            if 'Craft' in item_data:
                desc_parts.append(f"Craft: {item_data['Craft']}")
            
            desc = '. '.join(desc_parts) if desc_parts else f"A {name.lower()}."
            
            item = {
                "model": "api_v2.item",
                "pk": item_pk,
                "fields": {
                    "name": name,
                    "desc": desc,
                    "document": "srd-2024",
                    "size": "tiny",
                    "weight": weight,
                    "armor_class": 0,
                    "hit_points": 0,
                    "hit_dice": None,
                    "nonmagical_attack_resistance": False,
                    "nonmagical_attack_immunity": False,
                    "cost": cost,
                    "weapon": None,
                    "armor": None,
                    "category": category,
                    "requires_attunement": False,
                    "rarity": None,
                    "damage_vulnerabilities": [],
                    "damage_immunities": ["poison", "psychic"],
                    "damage_resistances": []
                }
            }
            
            items.append(item)
    
    return items

def create_item_categories() -> List[Dict[str, Any]]:
    """Create only new item categories not already in 2014 SRD."""
    # Categories have already been added to the 2014 ItemCategory.json
    # No need to create separate 2024 categories
    return []

def create_item_sets(weapons: List[Dict], armors: List[Dict], items: List[Dict]) -> List[Dict[str, Any]]:
    """Create new item sets for SRD 2024 that don't conflict with 2014."""
    sets = []
    
    # Create new weapon mastery sets (unique to 2024)
    mastery_groups = {}
    for weapon in weapons:
        mastery = weapon['fields'].get('mastery', '')
        if mastery and mastery != 'None':
            if mastery not in mastery_groups:
                mastery_groups[mastery] = []
            mastery_groups[mastery].append(weapon['pk'])
    
    for mastery, weapon_pks in mastery_groups.items():
        if weapon_pks:  # Only create if there are weapons with this mastery
            sets.append({
                "model": "api_v2.itemset",
                "pk": f"{mastery.lower()}-mastery-weapons-2024",
                "fields": {
                    "name": f"{mastery} Mastery Weapons",
                    "desc": f"Weapons with the {mastery} mastery property in the 2024 rules.",
                    "document": "srd-2024",
                    "items": weapon_pks
                }
            })
    
    # Note: Item sets for services, mounts, and vehicles are handled in the 2014 files
    # No need to create separate 2024 sets for these categories
    
    return sets

def generate_2014_itemset_updates(weapons: List[Dict]) -> Dict[str, List[str]]:
    """Generate updates for existing 2014 ItemSet.json to include 2024 weapons."""
    updates = {}
    
    # Categorize 2024 weapons
    simple_melee = [w['pk'] for w in weapons if w['fields']['is_simple'] and w['fields']['range'] == 0.0]
    simple_ranged = [w['pk'] for w in weapons if w['fields']['is_simple'] and w['fields']['range'] > 0.0]
    martial_melee = [w['pk'] for w in weapons if not w['fields']['is_simple'] and w['fields']['range'] == 0.0]
    martial_ranged = [w['pk'] for w in weapons if not w['fields']['is_simple'] and w['fields']['range'] > 0.0]
    
    updates['simple-melee-weapons'] = simple_melee
    updates['simple-ranged-weapons'] = simple_ranged
    updates['martial-melee-weapons'] = martial_melee
    updates['martial-ranged-weapons'] = martial_ranged
    
    return updates

def generate_2014_itemset_updates_for_armor(armors: List[Dict]) -> Dict[str, List[str]]:
    """Generate updates for existing 2014 ItemSet.json to include 2024 armor."""
    updates = {}
    
    # Categorize 2024 armor
    light_armor = [a['pk'] for a in armors if 'light' in a['fields']['name'].lower()]
    medium_armor = [a['pk'] for a in armors if any(name in a['fields']['name'].lower() for name in ['hide', 'chain shirt', 'scale', 'breastplate', 'half plate'])]
    heavy_armor = [a['pk'] for a in armors if any(name in a['fields']['name'].lower() for name in ['ring mail', 'chain mail', 'splint', 'plate'])]
    
    updates['light-armor'] = light_armor
    updates['medium-armor'] = medium_armor
    updates['heavy-armor'] = heavy_armor
    
    return updates

def generate_2014_itemset_updates_for_tools(items: List[Dict]) -> Dict[str, List[str]]:
    """Generate updates for existing 2014 ItemSet.json to include 2024 tools."""
    updates = {}
    
    # Find artisan tools
    artisan_tools = [i['pk'] for i in items if i['fields']['category'] == 'tools' and 
                     ('supplies' in i['fields']['name'].lower() or 'tools' in i['fields']['name'].lower())]
    
    if artisan_tools:
        updates['artisans-tools'] = artisan_tools
    
    return updates

def main():
    """Main function to convert equipment."""
    # Input files
    weapons_file = Path("../sections/07_weapons_items.md")
    armor_file = Path("../sections/07_armor_items.md")
    tools_file = Path("../sections/07_tools_items.md")
    services_file = Path("../sections/07_services_items.md")
    mounts_file = Path("../sections/07_mounts_vehicles_items.md")
    magic_items_file = Path("../sections/07_magic_items.md")
    
    # Output directory
    output_dir = Path("../../../v2/wizards-of-the-coast/srd-2024/")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Converting SRD 5.2 equipment...")
    
    # Convert weapons
    if weapons_file.exists():
        weapons, weapon_items, weapon_properties, property_assignments = convert_weapons(weapons_file)
        print(f"Converted {len(weapons)} weapons")
        print(f"Created {len(weapon_items)} weapon items")
        print(f"Created {len(weapon_properties)} weapon properties")
        print(f"Generated {len(property_assignments)} property assignments")
    else:
        weapons, weapon_items, weapon_properties, property_assignments = [], [], [], []
        print("Weapons file not found")
    
    # Convert armor
    if armor_file.exists():
        armors, armor_items = convert_armor(armor_file)
        print(f"Converted {len(armors)} armor pieces")
        print(f"Created {len(armor_items)} armor items")
    else:
        armors, armor_items = [], []
        print("Armor file not found")
    
    # Convert magic items (separate from other items)
    magic_items = convert_magic_items(magic_items_file)
    print(f"Converted {len(magic_items)} magic items")
    
    # Convert other items (tools, services, mounts)
    item_files = [f for f in [tools_file, services_file, mounts_file] if f.exists()]
    other_items = convert_items(item_files)
    print(f"Converted {len(other_items)} other items from {len(item_files)} files")
    
    # Combine all items (weapons, armor, magic items, and other items)
    all_items = weapon_items + armor_items + magic_items + other_items
    print(f"Total items: {len(all_items)}")
    
    # Create categories and sets
    categories = create_item_categories()
    sets = create_item_sets(weapons, armors, other_items)
    
    # Generate updates for 2014 ItemSet.json
    weapon_updates = generate_2014_itemset_updates(weapons) if weapons else {}
    armor_updates = generate_2014_itemset_updates_for_armor(armors) if armors else {}
    tool_updates = generate_2014_itemset_updates_for_tools(other_items) if other_items else {}
    
    print(f"Created {len(categories)} item categories")
    print(f"Created {len(sets)} item sets")
    print(f"Generated updates for {len(weapon_updates)} weapon sets in 2014")
    print(f"Generated updates for {len(armor_updates)} armor sets in 2014")
    print(f"Generated updates for {len(tool_updates)} tool sets in 2014")
    
    # Write output files
    files_written = []
    
    if weapons:
        weapons_file_out = output_dir / "Weapon.json"
        with open(weapons_file_out, 'w', encoding='utf-8') as f:
            json.dump(weapons, f, indent=2, ensure_ascii=False)
        files_written.append("Weapon.json")
    
    if armors:
        armor_file_out = output_dir / "Armor.json"
        with open(armor_file_out, 'w', encoding='utf-8') as f:
            json.dump(armors, f, indent=2, ensure_ascii=False)
        files_written.append("Armor.json")
    
    if weapon_properties:
        properties_file_out = output_dir / "WeaponProperty.json"
        with open(properties_file_out, 'w', encoding='utf-8') as f:
            json.dump(weapon_properties, f, indent=2, ensure_ascii=False)
        files_written.append("WeaponProperty.json")
    
    if property_assignments:
        assignments_file_out = output_dir / "WeaponPropertyAssignment.json"
        with open(assignments_file_out, 'w', encoding='utf-8') as f:
            json.dump(property_assignments, f, indent=2, ensure_ascii=False)
        files_written.append("WeaponPropertyAssignment.json")
    
    if all_items:
        items_file_out = output_dir / "Item.json"
        with open(items_file_out, 'w', encoding='utf-8') as f:
            json.dump(all_items, f, indent=2, ensure_ascii=False)
        files_written.append("Item.json")
    
    if categories:
        categories_file_out = output_dir / "ItemCategory.json"
        with open(categories_file_out, 'w', encoding='utf-8') as f:
            json.dump(categories, f, indent=2, ensure_ascii=False)
        files_written.append("ItemCategory.json")
    
    if sets:
        sets_file_out = output_dir / "ItemSet.json"
        with open(sets_file_out, 'w', encoding='utf-8') as f:
            json.dump(sets, f, indent=2, ensure_ascii=False)
        files_written.append("ItemSet.json")
    
    # Note: 2014 ItemSet.json has already been manually updated with 2024 items
    # No need to generate the updates file anymore
    
    print(f"\nConversion completed!")
    print(f"Files written to {output_dir}:")
    for filename in files_written:
        print(f"  - {filename}")
    
    print(f"\nNote: 2014 ItemSet.json has already been updated with 2024 items.")

if __name__ == "__main__":
    main() 