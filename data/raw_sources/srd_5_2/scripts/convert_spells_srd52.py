#!/usr/bin/env python3
"""
Enhanced SRD 5.2 Spell Converter

This script converts spells from the D&D SRD 5.2 markdown format to Open5e API v2 JSON format,
with enhanced parsing to extract damage rolls, saving throws, attack rolls, and area effects
from spell descriptions.
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

def parse_casting_time(casting_time: str) -> tuple[str, Optional[str]]:
    """Parse casting time and extract reaction condition if present."""
    casting_time = clean_text(casting_time)
    
    # Check for reaction
    if "Reaction" in casting_time:
        # Extract reaction condition if present
        reaction_match = re.search(r'Reaction\s*\((.*?)\)', casting_time)
        if reaction_match:
            return "reaction", reaction_match.group(1)
        return "reaction", None
    
    # Check for bonus action
    if "Bonus Action" in casting_time:
        return "bonus_action", None
    
    # Check for ritual
    if "Ritual" in casting_time:
        if "1 minute" in casting_time:
            return "minute", None
        return "action", None
    
    # Check for time-based casting
    if "minute" in casting_time.lower():
        return "minute", None
    if "hour" in casting_time.lower():
        return "hour", None
    
    # Default to action
    return "action", None

def parse_range(range_text: str) -> tuple[float, Optional[str], str]:
    """Parse range and return value, unit, and cleaned text."""
    range_text = clean_text(range_text)
    
    if "Self" in range_text:
        return 0.0, None, "Self"
    if "Touch" in range_text:
        return 0.0, None, "Touch"
    
    # Extract numeric range
    range_match = re.search(r'(\d+)\s*feet', range_text)
    if range_match:
        return float(range_match.group(1)), "feet", range_text
    
    # Extract mile range
    mile_match = re.search(r'(\d+)\s*mile', range_text)
    if mile_match:
        return float(mile_match.group(1)) * 5280, "feet", range_text
    
    return 0.0, None, range_text

def parse_components(components: str) -> tuple[bool, bool, bool, str, Optional[int], bool]:
    """Parse components and return V, S, M, material_specified, material_cost, material_consumed."""
    components = clean_text(components)
    
    verbal = "V" in components
    somatic = "S" in components
    material = "M" in components
    
    material_specified = ""
    material_cost = None
    material_consumed = False
    
    if material:
        # Extract material component details
        material_match = re.search(r'M\s*\((.*?)\)', components)
        if material_match:
            material_text = material_match.group(1)
            material_specified = material_text
            
            # Check for cost
            cost_match = re.search(r'(\d+)\s*gp', material_text)
            if cost_match:
                material_cost = int(cost_match.group(1))
            
            # Check if consumed
            if "consume" in material_text.lower() or "worth" in material_text.lower():
                material_consumed = True
    
    return verbal, somatic, material, material_specified, material_cost, material_consumed

def parse_duration(duration: str) -> tuple[str, bool]:
    """Parse duration and return duration string and concentration flag."""
    duration = clean_text(duration)
    
    concentration = "Concentration" in duration
    
    if "Instantaneous" in duration:
        return "instantaneous", concentration
    if "Permanent" in duration:
        return "permanent", concentration
    
    # Extract time-based duration
    time_match = re.search(r'(\d+)\s*(round|minute|hour|day)', duration)
    if time_match:
        return f"{time_match.group(1)} {time_match.group(2)}", concentration
    
    return duration.lower(), concentration

def parse_classes(class_text: str) -> List[str]:
    """Parse class list from text."""
    if not class_text:
        return []
    
    # Split by comma and clean up
    classes = [cls.strip() for cls in class_text.split(',')]
    
    # Map to SRD 2024 class keys
    class_mapping = {
        "Artificer": "srd-2024_artificer",
        "Bard": "srd-2024_bard", 
        "Cleric": "srd-2024_cleric",
        "Druid": "srd-2024_druid",
        "Paladin": "srd-2024_paladin",
        "Ranger": "srd-2024_ranger",
        "Sorcerer": "srd-2024_sorcerer",
        "Warlock": "srd-2024_warlock",
        "Wizard": "srd-2024_wizard"
    }
    
    result = []
    for cls in classes:
        if cls in class_mapping:
            result.append(class_mapping[cls])
    
    return result

def parse_school(school_text: str) -> str:
    """Parse school from text."""
    schools = ["Abjuration", "Conjuration", "Divination", "Enchantment", 
               "Evocation", "Illusion", "Necromancy", "Transmutation"]
    
    for school in schools:
        if school in school_text:
            return school.lower()
    
    return "evocation"  # default

def parse_spell_level(level_text: str) -> int:
    """Parse spell level from text."""
    if "Cantrip" in level_text:
        return 0
    
    # Extract level number
    match = re.search(r'Level (\d+)', level_text)
    if match:
        return int(match.group(1))
    
    return 0

def create_spell_pk(name: str) -> str:
    """Create primary key for spell."""
    # Convert to lowercase, replace spaces with hyphens, remove special chars
    pk = re.sub(r'[^\w\s-]', '', name.lower())
    pk = re.sub(r'[-\s]+', '-', pk)
    return f"srd-2024_{pk}"

def parse_spell_header(header_line: str) -> tuple[int, str, List[str]]:
    """Parse the spell header line to extract level, school, and classes."""
    header_line = clean_text(header_line)
    
    # Remove italic markers
    header_line = header_line.strip('*')
    
    # Parse level
    level = 0
    if "Cantrip" in header_line:
        level = 0
    else:
        level_match = re.search(r'Level (\d+)', header_line)
        if level_match:
            level = int(level_match.group(1))
    
    # Parse school
    school = "evocation"  # default
    schools = ["Abjuration", "Conjuration", "Divination", "Enchantment", 
               "Evocation", "Illusion", "Necromancy", "Transmutation"]
    for s in schools:
        if s in header_line:
            school = s.lower()
            break
    
    # Parse classes - they appear in parentheses at the end
    classes = []
    class_match = re.search(r'\((.*?)\)', header_line)
    if class_match:
        class_text = class_match.group(1)
        classes = parse_classes(class_text)
    
    return level, school, classes

def extract_attack_roll(description: str) -> bool:
    """Extract whether spell requires an attack roll."""
    attack_patterns = [
        r'make a (?:ranged|melee) spell attack',
        r'spell attack roll',
        r'attack roll'
    ]
    
    for pattern in attack_patterns:
        if re.search(pattern, description, re.IGNORECASE):
            return True
    
    return False

def extract_saving_throw(description: str) -> str:
    """Extract saving throw ability from description."""
    save_patterns = [
        r'(\w+) saving throw',
        r'succeed on a (\w+) save'
    ]
    
    for pattern in save_patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            ability = match.group(1).lower()
            # Map to standard ability names
            ability_mapping = {
                "strength": "strength",
                "dexterity": "dexterity", 
                "constitution": "constitution",
                "intelligence": "intelligence",
                "wisdom": "wisdom",
                "charisma": "charisma"
            }
            return ability_mapping.get(ability, "")
    
    return ""

def extract_damage_info(description: str) -> tuple[str, List[str]]:
    """Extract damage roll and damage types from description."""
    damage_roll = ""
    damage_types = []
    
    # Extract damage roll (dice notation)
    damage_patterns = [
        r'(\d+d\d+(?:\s*\+\s*\d+)?)',  # Basic dice notation
        r'takes (\d+d\d+)',             # "takes XdY damage"
        r'deals (\d+d\d+)'              # "deals XdY damage"
    ]
    
    for pattern in damage_patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            damage_roll = match.group(1)
            break
    
    # Extract damage types
    damage_type_patterns = [
        r'(\w+) damage',
        r'damage of the (\w+) type'
    ]
    
    found_types = set()
    for pattern in damage_type_patterns:
        matches = re.finditer(pattern, description, re.IGNORECASE)
        for match in matches:
            damage_type = match.group(1).lower()
            # Map to standard damage types
            type_mapping = {
                "acid": "acid",
                "bludgeoning": "bludgeoning",
                "cold": "cold",
                "fire": "fire",
                "force": "force",
                "lightning": "lightning",
                "necrotic": "necrotic",
                "piercing": "piercing",
                "poison": "poison",
                "psychic": "psychic",
                "radiant": "radiant",
                "slashing": "slashing",
                "thunder": "thunder"
            }
            if damage_type in type_mapping:
                found_types.add(type_mapping[damage_type])
    
    damage_types = list(found_types)
    
    return damage_roll, damage_types

def extract_shape_info(description: str) -> tuple[Optional[str], Optional[float]]:
    """Extract area of effect shape and size from description."""
    shape_type = None
    shape_size = None
    
    # Shape patterns
    shape_patterns = [
        (r'(\d+)-foot-radius (sphere|circle)', 'sphere'),
        (r'(\d+)-foot (cube)', 'cube'),
        (r'(\d+)-foot (cone)', 'cone'),
        (r'(\d+)-foot (line)', 'line'),
        (r'(\d+)-foot-wide (line)', 'line'),
        (r'(\d+)-foot (cylinder)', 'cylinder'),
        (r'(\d+) by (\d+) foot', 'rectangle')
    ]
    
    for pattern, shape in shape_patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            shape_type = shape
            shape_size = float(match.group(1))
            break
    
    return shape_type, shape_size

def parse_spells_from_markdown(file_path: Path) -> List[Dict[str, Any]]:
    """Parse spells from the markdown file with enhanced extraction."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    spells = []
    
    # Split by spell headers (#### Spell Name)
    spell_sections = re.split(r'\n#### ', content)
    
    for section in spell_sections[1:]:  # Skip first section (before first spell)
        lines = section.strip().split('\n')
        if not lines:
            continue
            
        # Parse spell name - remove any markdown formatting
        spell_name = clean_text(lines[0].strip())
        if not spell_name:
            continue
        
        print(f"Processing spell: {spell_name}")
        
        # Initialize variables
        header_line = ""
        casting_time = ""
        range_text = ""
        components = ""
        duration = ""
        description_lines = []
        higher_level = ""
        
        # Parse the spell data
        i = 1
        in_description = False
        found_header = False
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for the spell header (italic line with Level/Cantrip and school)
            if line.startswith('*') and ('Level' in line or 'Cantrip' in line) and not found_header:
                header_line = line
                found_header = True
                in_description = False
            elif line.startswith('**Casting Time:**'):
                casting_time = line.replace('**Casting Time:**', '').strip()
                in_description = False
            elif line.startswith('**Range:**'):
                range_text = line.replace('**Range:**', '').strip()
                in_description = False
            elif line.startswith('**Components:**'):
                components = line.replace('**Components:**', '').strip()
                in_description = False
            elif line.startswith('**Duration:**'):
                duration = line.replace('**Duration:**', '').strip()
                in_description = True  # Description starts after duration
            elif line.startswith('**_Using a Higher-Level Spell Slot._**') or line.startswith('**_Cantrip Upgrade._**'):
                higher_level = line.replace('**_Using a Higher-Level Spell Slot._**', '').replace('**_Cantrip Upgrade._**', '').strip()
                in_description = False
            elif in_description and line and not line.startswith('**') and not line.startswith('*') and not line.startswith('>'):
                # This is part of the description
                description_lines.append(line)
            elif line.startswith('**_') and any(keyword in line for keyword in ['Aquatic Adaptation', 'Change Appearance', 'Natural Weapons', 'Audible Alarm', 'Mental Alarm']):
                # Special case for spell options
                description_lines.append(line)
            
            i += 1
        
        description = " ".join(description_lines)
        
        if not header_line:
            print(f"  Warning: No header found for {spell_name}")
            continue
        
        # Parse header with improved parsing
        level, school, classes = parse_spell_header(header_line)
        
        # Parse other fields
        casting_time_parsed, reaction_condition = parse_casting_time(casting_time)
        range_val, range_unit, range_text_clean = parse_range(range_text)
        verbal, somatic, material, material_specified, material_cost, material_consumed = parse_components(components)
        duration_parsed, concentration = parse_duration(duration)
        
        # Enhanced extraction from description
        attack_roll = extract_attack_roll(description)
        saving_throw_ability = extract_saving_throw(description)
        damage_roll, damage_types = extract_damage_info(description)
        shape_type, shape_size = extract_shape_info(description)
        
        # Debug output for enhanced fields
        if attack_roll:
            print(f"  Found attack roll: {spell_name}")
        if saving_throw_ability:
            print(f"  Found saving throw ({saving_throw_ability}): {spell_name}")
        if damage_roll:
            print(f"  Found damage roll ({damage_roll}): {spell_name}")
        if damage_types:
            print(f"  Found damage types ({damage_types}): {spell_name}")
        if shape_type:
            print(f"  Found shape ({shape_type}, {shape_size}): {spell_name}")
        
        # Create spell object
        spell = {
            "model": "api_v2.spell",
            "pk": create_spell_pk(spell_name),
            "fields": {
                "name": spell_name,
                "desc": clean_text(description),
                "document": "srd-2024",
                "level": level,
                "school": school,
                "higher_level": clean_text(higher_level),
                "target_type": "creature",  # Default, would need more parsing to determine
                "range_text": range_text_clean,
                "range": range_val,
                "range_unit": range_unit,
                "ritual": "Ritual" in casting_time,
                "casting_time": casting_time_parsed,
                "reaction_condition": reaction_condition,
                "verbal": verbal,
                "somatic": somatic,
                "material": material,
                "material_specified": material_specified,
                "material_cost": material_cost,
                "material_consumed": material_consumed,
                "target_count": 1,  # Default, would need more parsing
                "saving_throw_ability": saving_throw_ability,
                "attack_roll": attack_roll,
                "damage_roll": damage_roll,
                "damage_types": damage_types,
                "duration": duration_parsed,
                "shape_type": shape_type,
                "shape_size": shape_size,
                "shape_size_unit": "feet" if shape_size else None,
                "concentration": concentration,
                "classes": classes
            }
        }
        
        spells.append(spell)
    
    return spells

def main():
    """Main function to convert spells."""
    input_file = Path("../sections/08_b_spellsaz.md")
    output_file = Path("../../../v2/wizards-of-the-coast/srd-2024/Spell.json")
    
    print(f"Converting spells from {input_file} to {output_file}")
    
    spells = parse_spells_from_markdown(input_file)
    
    print(f"Converted {len(spells)} spells")
    
    # Write to JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(spells, f, indent=2, ensure_ascii=False)
    
    print(f"Spells written to {output_file}")

if __name__ == "__main__":
    main() 