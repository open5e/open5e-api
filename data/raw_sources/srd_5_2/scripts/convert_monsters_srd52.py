#!/usr/bin/env python3
"""
SRD 5.2 Monster Converter

This script converts monsters from the D&D SRD 5.2 markdown format to Open5e API v2 JSON format,
creating separate files for Creature, CreatureAction, and CreatureTrait data.
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

def create_creature_pk(name: str) -> str:
    """Create primary key for creature."""
    # Convert to lowercase, replace spaces with hyphens, remove special chars
    pk = re.sub(r'[^\w\s-]', '', name.lower())
    pk = re.sub(r'[-\s]+', '-', pk)
    return f"srd2024_{pk}"

def parse_ability_scores(stats_table: str) -> Dict[str, int]:
    """Parse ability scores from the stats table."""
    scores = {}
    
    # Look for the table format - each stat is on its own line
    lines = stats_table.split('\n')
    for line in lines:
        if '|' in line:
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if len(parts) >= 4:
                try:
                    stat = parts[0].upper()
                    score = int(parts[1])
                    
                    if stat == 'STR':
                        scores['strength'] = score
                    elif stat == 'DEX':
                        scores['dexterity'] = score
                    elif stat == 'CON':
                        scores['constitution'] = score
                    elif stat == 'INT':
                        scores['intelligence'] = score
                    elif stat == 'WIS':
                        scores['wisdom'] = score
                    elif stat == 'CHA':
                        scores['charisma'] = score
                except (ValueError, IndexError):
                    continue
    
    return scores

def parse_saving_throws(stats_table: str) -> Dict[str, Optional[int]]:
    """Parse saving throws from the stats table."""
    saves = {}
    
    # Look for saving throws in the individual stat lines
    lines = stats_table.split('\n')
    for line in lines:
        if '|' in line:
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if len(parts) >= 4:
                try:
                    stat = parts[0].upper()
                    save_val = parts[3]  # SAVE column
                    
                    # Parse save value (could be +5, -1, etc.)
                    save_int = None
                    if save_val and save_val not in ['-', '']:
                        save_int = int(save_val.replace('+', ''))
                    
                    if stat == 'STR':
                        saves['strength'] = save_int
                    elif stat == 'DEX':
                        saves['dexterity'] = save_int
                    elif stat == 'CON':
                        saves['constitution'] = save_int
                    elif stat == 'INT':
                        saves['intelligence'] = save_int
                    elif stat == 'WIS':
                        saves['wisdom'] = save_int
                    elif stat == 'CHA':
                        saves['charisma'] = save_int
                except (ValueError, IndexError):
                    continue
    
    return saves

def parse_skills(text: str) -> Dict[str, Optional[int]]:
    """Parse skill bonuses from text."""
    skills = {}
    
    # Initialize all skills to None
    skill_names = [
        'acrobatics', 'animal_handling', 'arcana', 'athletics', 'deception',
        'history', 'insight', 'intimidation', 'investigation', 'medicine',
        'nature', 'perception', 'performance', 'persuasion', 'religion',
        'sleight_of_hand', 'stealth', 'survival'
    ]
    
    for skill in skill_names:
        skills[f'skill_bonus_{skill}'] = None
    
    # Look for skills line
    skills_match = re.search(r'- \*\*Skills\*\*:?\s*([^\n]+)', text, re.IGNORECASE)
    if skills_match:
        skills_text = skills_match.group(1)
        
        # Parse individual skills
        skill_patterns = {
            'history': r'History\s*\+(\d+)',
            'perception': r'Perception\s*\+(\d+)',
            'stealth': r'Stealth\s*\+(\d+)',
            'intimidation': r'Intimidation\s*\+(\d+)',
            'persuasion': r'Persuasion\s*\+(\d+)',
            'athletics': r'Athletics\s*\+(\d+)',
            'acrobatics': r'Acrobatics\s*\+(\d+)',
            'arcana': r'Arcana\s*\+(\d+)',
            'deception': r'Deception\s*\+(\d+)',
            'insight': r'Insight\s*\+(\d+)',
            'investigation': r'Investigation\s*\+(\d+)',
            'medicine': r'Medicine\s*\+(\d+)',
            'nature': r'Nature\s*\+(\d+)',
            'performance': r'Performance\s*\+(\d+)',
            'religion': r'Religion\s*\+(\d+)',
            'sleight_of_hand': r'Sleight of Hand\s*\+(\d+)',
            'survival': r'Survival\s*\+(\d+)',
            'animal_handling': r'Animal Handling\s*\+(\d+)'
        }
        
        for skill, pattern in skill_patterns.items():
            match = re.search(pattern, skills_text, re.IGNORECASE)
            if match:
                skills[f'skill_bonus_{skill}'] = int(match.group(1))
    
    return skills

def parse_senses(text: str) -> Dict[str, Optional[float]]:
    """Parse senses from text."""
    senses = {
        'darkvision_range': None,
        'blindsight_range': None,
        'tremorsense_range': None,
        'truesight_range': None,
        'passive_perception': 10
    }
    
    # Look for senses line
    senses_match = re.search(r'- \*\*Senses\*\*:?\s*([^\n]+)', text, re.IGNORECASE)
    if senses_match:
        senses_text = senses_match.group(1)
        
        # Parse different vision types
        darkvision_match = re.search(r'darkvision\s+(\d+)\s*ft', senses_text, re.IGNORECASE)
        if darkvision_match:
            senses['darkvision_range'] = float(darkvision_match.group(1))
        
        blindsight_match = re.search(r'blindsight\s+(\d+)\s*ft', senses_text, re.IGNORECASE)
        if blindsight_match:
            senses['blindsight_range'] = float(blindsight_match.group(1))
        
        tremorsense_match = re.search(r'tremorsense\s+(\d+)\s*ft', senses_text, re.IGNORECASE)
        if tremorsense_match:
            senses['tremorsense_range'] = float(tremorsense_match.group(1))
        
        truesight_match = re.search(r'truesight\s+(\d+)\s*ft', senses_text, re.IGNORECASE)
        if truesight_match:
            senses['truesight_range'] = float(truesight_match.group(1))
        
        # Parse passive perception
        passive_match = re.search(r'passive\s+perception\s+(\d+)', senses_text, re.IGNORECASE)
        if passive_match:
            senses['passive_perception'] = int(passive_match.group(1))
    
    return senses

def parse_languages(text: str) -> Tuple[List[str], str, Optional[float]]:
    """Parse languages from text, returning language keys, description, and telepathy range."""
    languages = []
    telepathy_range = None
    
    # Look for languages line
    lang_match = re.search(r'- \*\*Languages\*\*:?\s*([^\n]+)', text, re.IGNORECASE)
    if lang_match:
        lang_text = lang_match.group(1)
        lang_desc = clean_text(lang_text)
        
        # Parse telepathy
        telepathy_match = re.search(r'telepathy\s+(\d+)\s*ft', lang_text, re.IGNORECASE)
        if telepathy_match:
            telepathy_range = float(telepathy_match.group(1))
        
        # Map common languages to keys
        language_mapping = {
            'common': 'common',
            'draconic': 'draconic',
            'deep speech': 'deep-speech',
            'giant': 'giant',
            'goblin': 'goblin',
            'orc': 'orc',
            'elvish': 'elvish',
            'dwarvish': 'dwarvish',
            'halfling': 'halfling',
            'gnomish': 'gnomish',
            'abyssal': 'abyssal',
            'celestial': 'celestial',
            'infernal': 'infernal',
            'primordial': 'primordial',
            'sylvan': 'sylvan',
            'undercommon': 'undercommon'
        }
        
        for lang_name, lang_key in language_mapping.items():
            if lang_name.lower() in lang_text.lower():
                languages.append(lang_key)
        
        return languages, lang_desc, telepathy_range
    
    return [], "", None

def parse_speed(text: str) -> Dict[str, Optional[float]]:
    """Parse speed from text."""
    speeds = {
        'walk': 30.0,  # Default walking speed
        'fly': None,
        'swim': None,
        'burrow': None,
        'climb': None,
        'hover': False
    }
    
    # Look for speed line
    speed_match = re.search(r'- \*\*Speed:\*\*\s*([^\n]+)', text, re.IGNORECASE)
    if speed_match:
        speed_text = speed_match.group(1)
        
        # Parse walking speed (first number)
        walk_match = re.search(r'^(\d+)\s*ft', speed_text.strip())
        if walk_match:
            speeds['walk'] = float(walk_match.group(1))
        
        # Parse other speeds
        fly_match = re.search(r'Fly\s+(\d+)\s*ft', speed_text, re.IGNORECASE)
        if fly_match:
            speeds['fly'] = float(fly_match.group(1))
            if 'hover' in speed_text.lower():
                speeds['hover'] = True
        
        swim_match = re.search(r'Swim\s+(\d+)\s*ft', speed_text, re.IGNORECASE)
        if swim_match:
            speeds['swim'] = float(swim_match.group(1))
        
        burrow_match = re.search(r'Burrow\s+(\d+)\s*ft', speed_text, re.IGNORECASE)
        if burrow_match:
            speeds['burrow'] = float(burrow_match.group(1))
        
        climb_match = re.search(r'Climb\s+(\d+)\s*ft', speed_text, re.IGNORECASE)
        if climb_match:
            speeds['climb'] = float(climb_match.group(1))
    
    return speeds

def parse_damage_resistances_immunities(text: str) -> Tuple[List[str], List[str], List[str], List[str]]:
    """Parse damage resistances, immunities, vulnerabilities, and condition immunities."""
    resistances = []
    immunities = []
    vulnerabilities = []
    condition_immunities = []
    
    # Damage resistances
    resist_match = re.search(r'- \*\*Resistances?\*\*:?\s*([^\n]+)', text, re.IGNORECASE)
    if resist_match:
        resist_text = resist_match.group(1).lower()
        damage_types = ['acid', 'cold', 'fire', 'force', 'lightning', 'necrotic', 'poison', 'psychic', 'radiant', 'thunder']
        for dtype in damage_types:
            if dtype in resist_text:
                resistances.append(dtype)
    
    # Damage immunities - SRD 2024 format: "Fire, Poison, Psychic; Charmed, Exhaustion, Frightened"
    immune_match = re.search(r'- \*\*Immunities?\*\*:?\s*([^\n]+)', text, re.IGNORECASE)
    if immune_match:
        immune_text = immune_match.group(1)
        
        # Split by semicolon - first part is damage immunities, second part is condition immunities
        parts = immune_text.split(';')
        
        # Parse damage immunities (first part)
        if len(parts) > 0:
            damage_part = parts[0].lower()
            damage_types = ['acid', 'cold', 'fire', 'force', 'lightning', 'necrotic', 'poison', 'psychic', 'radiant', 'thunder']
            for dtype in damage_types:
                if dtype in damage_part:
                    immunities.append(dtype)
        
        # Parse condition immunities (second part, if exists)
        if len(parts) > 1:
            condition_part = parts[1].lower()
            conditions = ['blinded', 'charmed', 'deafened', 'exhaustion', 'frightened', 'grappled', 'incapacitated', 'invisible', 'paralyzed', 'petrified', 'poisoned', 'prone', 'restrained', 'stunned', 'unconscious']
            for condition in conditions:
                if condition in condition_part:
                    condition_immunities.append(condition)
    
    # Also check for separate condition immunities line (for backward compatibility)
    cond_immune_match = re.search(r'condition\s+immunities?\*\*:?\s*([^\n]+)', text, re.IGNORECASE)
    if cond_immune_match:
        cond_text = cond_immune_match.group(1).lower()
        conditions = ['blinded', 'charmed', 'deafened', 'exhaustion', 'frightened', 'grappled', 'incapacitated', 'invisible', 'paralyzed', 'petrified', 'poisoned', 'prone', 'restrained', 'stunned', 'unconscious']
        for condition in conditions:
            if condition in cond_text:
                condition_immunities.append(condition)
    
    return resistances, immunities, vulnerabilities, condition_immunities

def parse_creature_type_and_alignment(header: str) -> Tuple[str, str, str]:
    """Parse creature type, size, and alignment from header."""
    # Example: "*Large Aberration, Lawful Evil*"
    header = clean_text(header)
    
    size = "medium"  # default
    creature_type = "humanoid"  # default
    alignment = "neutral"  # default
    
    # Parse size
    sizes = ['tiny', 'small', 'medium', 'large', 'huge', 'gargantuan']
    for s in sizes:
        if s.lower() in header.lower():
            size = s.lower()
            break
    
    # Parse creature type
    types = ['aberration', 'beast', 'celestial', 'construct', 'dragon', 'elemental', 'fey', 'fiend', 'giant', 'humanoid', 'monstrosity', 'ooze', 'plant', 'undead']
    for t in types:
        if t.lower() in header.lower():
            creature_type = t.lower()
            break
    
    # Parse alignment
    if 'lawful evil' in header.lower():
        alignment = 'lawful evil'
    elif 'chaotic evil' in header.lower():
        alignment = 'chaotic evil'
    elif 'neutral evil' in header.lower():
        alignment = 'neutral evil'
    elif 'lawful good' in header.lower():
        alignment = 'lawful good'
    elif 'chaotic good' in header.lower():
        alignment = 'chaotic good'
    elif 'neutral good' in header.lower():
        alignment = 'neutral good'
    elif 'lawful neutral' in header.lower():
        alignment = 'lawful neutral'
    elif 'chaotic neutral' in header.lower():
        alignment = 'chaotic neutral'
    elif 'unaligned' in header.lower():
        alignment = 'unaligned'
    else:
        alignment = 'neutral'
    
    return size, creature_type, alignment

def parse_basic_stats(text: str) -> Dict[str, Any]:
    """Parse basic stats like AC, HP, CR, and Initiative."""
    stats = {}
    
    # Armor Class
    ac_match = re.search(r'- \*\*Armor Class:\*\*\s*(\d+)', text)
    if ac_match:
        stats['armor_class'] = int(ac_match.group(1))
    
    # Hit Points
    hp_match = re.search(r'- \*\*Hit Points:\*\*\s*(\d+)\s*\(([^)]+)\)', text)
    if hp_match:
        stats['hit_points'] = int(hp_match.group(1))
        stats['hit_dice'] = hp_match.group(2)
    
    # Challenge Rating
    cr_match = re.search(r'- \*\*CR\*\*\s*(\d+(?:\.\d+)?)', text)
    if cr_match:
        stats['challenge_rating_decimal'] = f"{float(cr_match.group(1)):.3f}"
    
    # Initiative - format: "- **Initiative**: +3 (13)"
    initiative_match = re.search(r'- \*\*Initiative\*\*:?\s*([+-]?\d+)', text)
    if initiative_match:
        stats['initiative_bonus'] = int(initiative_match.group(1))
    
    return stats

def parse_traits(text: str, creature_pk: str) -> List[Dict[str, Any]]:
    """Parse creature traits."""
    traits = []
    
    # Find traits section
    traits_match = re.search(r'### Traits\s*\n(.*?)(?=### |$)', text, re.DOTALL)
    if traits_match:
        traits_text = traits_match.group(1)
        
        # Split by trait headers (***Name.***)
        trait_pattern = r'\*\*\*([^*]+)\.\*\*\*\s*(.*?)(?=\*\*\*|$)'
        trait_matches = re.findall(trait_pattern, traits_text, re.DOTALL)
        
        for trait_name, trait_desc in trait_matches:
            trait_name = clean_text(trait_name)
            trait_desc = clean_text(trait_desc)
            
            if trait_name and trait_desc:
                trait_pk = f"{creature_pk}_{trait_name.lower().replace(' ', '-').replace('(', '').replace(')', '').replace('/', '-')}"
                
                traits.append({
                    "model": "api_v2.creaturetrait",
                    "pk": trait_pk,
                    "fields": {
                        "name": trait_name,
                        "desc": trait_desc,
                        "type": None,
                        "parent": creature_pk
                    }
                })
    
    return traits

def parse_attack_from_description(desc: str, action_name: str, action_pk: str) -> List[Dict[str, Any]]:
    """Parse attack data from action description."""
    attacks = []
    
    # SRD 2024 format: "Melee Attack Roll: +9, reach 15 ft. 12 (2d6 + 5) Bludgeoning damage."
    # SRD 2014 format: "Melee Weapon Attack: +9 to hit, reach 10 ft., one target. Hit: 12 (2d6 + 5) bludgeoning damage."
    
    # Check for attack patterns
    attack_patterns = [
        # SRD 2024 format - including "Melee or Ranged"
        r'(Melee(?:\s+or\s+Ranged)?|Ranged)\s+Attack\s+Roll:\s*([+-]?\d+),\s*(?:reach\s+(\d+)\s*ft\.?)?\s*(?:(?:or\s+)?range\s+(\d+)(?:/(\d+))?\s*ft\.?)?\s*(\d+)\s*\(([^)]+)\)\s*(\w+)\s+damage',
        # SRD 2014 format  
        r'(Melee|Ranged)\s+(?:Weapon|Spell)\s+Attack:\s*([+-]?\d+)\s+to\s+hit,\s*(?:reach\s+(\d+)\s*ft\.?)?\s*(?:range\s+(\d+)(?:/(\d+))?\s*ft\.?)?\s*.*?Hit:\s*(\d+)\s*\(([^)]+)\)\s*(\w+)\s+damage'
    ]
    
    for pattern in attack_patterns:
        match = re.search(pattern, desc, re.IGNORECASE)
        if match:
            attack_type = "WEAPON"  # Default to weapon
            to_hit_mod = int(match.group(2))
            
            # Parse reach/range
            reach = float(match.group(3)) if match.group(3) else None
            range_val = float(match.group(4)) if match.group(4) else None
            long_range = float(match.group(5)) if match.group(5) else None
            
            # Parse damage
            damage_formula = match.group(7)  # e.g., "2d6 + 5"
            damage_type = match.group(8).lower()
            
            # Parse damage formula
            damage_die_count = None
            damage_die_type = None
            damage_bonus = None
            
            damage_match = re.search(r'(\d+)d(\d+)(?:\s*[+-]\s*(\d+))?', damage_formula)
            if damage_match:
                damage_die_count = int(damage_match.group(1))
                damage_die_type = f"D{damage_match.group(2)}"
                if damage_match.group(3):
                    damage_bonus = int(damage_match.group(3))
            
            # Create attack object
            attack_pk = f"{action_pk}_{action_name.lower().replace(' ', '-').replace('(', '').replace(')', '').replace('/', '-')}-attack"
            
            attack = {
                "model": "api_v2.creatureactionattack",
                "pk": attack_pk,
                "fields": {
                    "name": f"{action_name} attack",
                    "parent": action_pk,
                    "attack_type": attack_type,
                    "to_hit_mod": to_hit_mod,
                    "reach": reach,
                    "range": range_val,
                    "long_range": long_range,
                    "distance_unit": None,
                    "target_creature_only": False,
                    "damage_die_count": damage_die_count,
                    "damage_die_type": damage_die_type,
                    "damage_bonus": damage_bonus,
                    "damage_type": None,  # Would need damage type mapping
                    "extra_damage_die_count": None,
                    "extra_damage_die_type": None,
                    "extra_damage_bonus": None,
                    "extra_damage_type": damage_type
                }
            }
            
            attacks.append(attack)
            break
    
    return attacks

def parse_actions(text: str, creature_pk: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Parse creature actions and return both actions and attacks."""
    actions = []
    all_attacks = []
    order = 0
    
    # Find actions section
    actions_match = re.search(r'### Actions\s*\n(.*?)(?=### |$)', text, re.DOTALL)
    if actions_match:
        actions_text = actions_match.group(1)
        
        # Split by action headers (***Name.***)
        action_pattern = r'\*\*\*([^*]+)\.\*\*\*\s*(.*?)(?=\*\*\*|$)'
        action_matches = re.findall(action_pattern, actions_text, re.DOTALL)
        
        for action_name, action_desc in action_matches:
            action_name = clean_text(action_name)
            action_desc = clean_text(action_desc)
            
            if action_name and action_desc:
                action_pk = f"{creature_pk}_{action_name.lower().replace(' ', '-').replace('(', '').replace(')', '').replace('/', '-')}"
                
                # Determine uses
                uses_type = None
                uses_param = None
                
                if 'recharge' in action_name.lower():
                    uses_type = "RECHARGE"
                    recharge_match = re.search(r'recharge\s+(\d+)', action_name.lower())
                    if recharge_match:
                        uses_param = int(recharge_match.group(1))
                elif '/day' in action_name.lower():
                    uses_type = "PER_DAY"
                    day_match = re.search(r'(\d+)/day', action_name.lower())
                    if day_match:
                        uses_param = int(day_match.group(1))
                
                actions.append({
                    "model": "api_v2.creatureaction",
                    "pk": action_pk,
                    "fields": {
                        "name": action_name,
                        "desc": action_desc,
                        "parent": creature_pk,
                        "uses_type": uses_type,
                        "uses_param": uses_param,
                        "action_type": "ACTION",
                        "form_condition": None,
                        "legendary_cost": 1,
                        "order": order
                    }
                })
                
                # Parse attacks from description
                attacks = parse_attack_from_description(action_desc, action_name, action_pk)
                all_attacks.extend(attacks)
                
                order += 1
    
    return actions, all_attacks

def parse_legendary_actions(text: str, creature_pk: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Parse legendary actions and return both actions and attacks."""
    actions = []
    all_attacks = []
    order = 0
    
    # Find legendary actions section
    legendary_match = re.search(r'### Legendary Actions\s*\n(.*?)(?=### |$)', text, re.DOTALL)
    if legendary_match:
        legendary_text = legendary_match.group(1)
        
        # Split by action headers (***Name.***)
        action_pattern = r'\*\*\*([^*]+)\.\*\*\*\s*(.*?)(?=\*\*\*|$)'
        action_matches = re.findall(action_pattern, legendary_text, re.DOTALL)
        
        for action_name, action_desc in action_matches:
            action_name = clean_text(action_name)
            action_desc = clean_text(action_desc)
            
            if action_name and action_desc:
                action_pk = f"{creature_pk}_{action_name.lower().replace(' ', '-').replace('(', '').replace(')', '').replace('/', '-')}"
                
                # Determine legendary cost
                legendary_cost = 1
                if 'costs 2' in action_desc.lower():
                    legendary_cost = 2
                elif 'costs 3' in action_desc.lower():
                    legendary_cost = 3
                
                actions.append({
                    "model": "api_v2.creatureaction",
                    "pk": action_pk,
                    "fields": {
                        "name": action_name,
                        "desc": action_desc,
                        "parent": creature_pk,
                        "uses_type": None,
                        "uses_param": None,
                        "action_type": "LEGENDARY_ACTION",
                        "form_condition": None,
                        "legendary_cost": legendary_cost,
                        "order": order
                    }
                })
                
                # Parse attacks from description
                attacks = parse_attack_from_description(action_desc, action_name, action_pk)
                all_attacks.extend(attacks)
                
                order += 1
    
    return actions, all_attacks

def parse_monster(monster_text: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Parse a single monster from text."""
    lines = monster_text.strip().split('\n')
    
    # Get monster name from header
    name_match = re.search(r'^## (.+)$', lines[0])
    if not name_match:
        return None, [], [], []
    
    name = clean_text(name_match.group(1))
    creature_pk = create_creature_pk(name)
    
    # Get type/size/alignment header
    type_header = ""
    for line in lines[1:5]:  # Check first few lines
        if line.startswith('*') and line.endswith('*'):
            type_header = line
            break
    
    size, creature_type, alignment = parse_creature_type_and_alignment(type_header)
    
    # Join all text for parsing
    full_text = '\n'.join(lines)
    
    # Parse ability scores from stats table
    ability_scores = parse_ability_scores(full_text)
    saving_throws = parse_saving_throws(full_text)
    skills = parse_skills(full_text)
    senses = parse_senses(full_text)
    languages, lang_desc, telepathy_range = parse_languages(full_text)
    speeds = parse_speed(full_text)
    resistances, immunities, vulnerabilities, condition_immunities = parse_damage_resistances_immunities(full_text)
    basic_stats = parse_basic_stats(full_text)
    
    # Create creature data
    creature_data = {
        "model": "api_v2.creature",
        "pk": creature_pk,
        "fields": {
            "name": name,
            "ability_score_strength": ability_scores.get('strength', 10),
            "ability_score_dexterity": ability_scores.get('dexterity', 10),
            "ability_score_constitution": ability_scores.get('constitution', 10),
            "ability_score_intelligence": ability_scores.get('intelligence', 10),
            "ability_score_wisdom": ability_scores.get('wisdom', 10),
            "ability_score_charisma": ability_scores.get('charisma', 10),
            "saving_throw_strength": saving_throws.get('strength'),
            "saving_throw_dexterity": saving_throws.get('dexterity'),
            "saving_throw_constitution": saving_throws.get('constitution'),
            "saving_throw_intelligence": saving_throws.get('intelligence'),
            "saving_throw_wisdom": saving_throws.get('wisdom'),
            "saving_throw_charisma": saving_throws.get('charisma'),
            **skills,
            "passive_perception": senses.get('passive_perception', 10),
            "normal_sight_range": 10560.0,  # 2 miles in feet
            "darkvision_range": senses.get('darkvision_range'),
            "blindsight_range": senses.get('blindsight_range'),
            "tremorsense_range": senses.get('tremorsense_range'),
            "truesight_range": senses.get('truesight_range'),
            "document": "srd-2024",
            "size": size,
            "weight": "0.000",
            "armor_class": basic_stats.get('armor_class', 10),
            "hit_points": basic_stats.get('hit_points', 1),
            "hit_dice": basic_stats.get('hit_dice', "1d8"),
            "initiative_bonus": basic_stats.get('initiative_bonus'),
            "nonmagical_attack_resistance": False,
            "nonmagical_attack_immunity": False,
            "languages_desc": lang_desc,
            "telepathy_range": telepathy_range,
            "walk": speeds.get('walk'),
            "unit": None,
            "hover": speeds.get('hover', False),
            "fly": speeds.get('fly'),
            "burrow": speeds.get('burrow'),
            "climb": speeds.get('climb'),
            "swim": speeds.get('swim'),
            "type": creature_type,
            "category": "Monsters",
            "subcategory": None,
            "alignment": alignment,
            "challenge_rating_decimal": basic_stats.get('challenge_rating_decimal', "0.125"),
            "experience_points_integer": None,
            "languages": languages,
            "damage_vulnerabilities": vulnerabilities,
            "damage_immunities": immunities,
            "damage_resistances": resistances,
            "condition_immunities": condition_immunities,
            "environments": [],  # Would need additional mapping
            "armor_detail": "natural armor",
            "damage_resistances_display": ", ".join(resistances),
            "damage_immunities_display": ", ".join(immunities),
            "damage_vulnerabilities_display": ", ".join(vulnerabilities),
            "condition_immunities_display": ", ".join(condition_immunities)
        }
    }
    
    # Parse traits and actions
    traits = parse_traits(full_text, creature_pk)
    actions, action_attacks = parse_actions(full_text, creature_pk)
    legendary_actions, legendary_attacks = parse_legendary_actions(full_text, creature_pk)
    
    all_actions = actions + legendary_actions
    all_attacks = action_attacks + legendary_attacks
    
    return creature_data, traits, all_actions, all_attacks

def main():
    """Main function to convert monsters."""
    input_file = Path("../sections/13_monsters_az.md")
    output_dir = Path("../../../v2/wizards-of-the-coast/srd-2024/")
    
    if not input_file.exists():
        print(f"Error: Input file {input_file} not found")
        return
    
    # Read the input file
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split into individual monsters by ## headers
    monster_sections = re.split(r'\n(?=## [^#])', content)
    
    creatures = []
    all_traits = []
    all_actions = []
    all_attacks = []
    
    print("Converting monsters...")
    
    for i, section in enumerate(monster_sections):
        if not section.strip() or section.startswith('# Monsters'):
            continue
        
        try:
            creature, traits, actions, attacks = parse_monster(section)
            if creature:
                creatures.append(creature)
                all_traits.extend(traits)
                all_actions.extend(actions)
                all_attacks.extend(attacks)
                print(f"Converted: {creature['fields']['name']}")
            else:
                print(f"Failed to parse monster in section {i}")
        except Exception as e:
            print(f"Error parsing monster in section {i}: {e}")
            continue
    
    # Write output files
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write creatures
    creatures_file = output_dir / "Creature.json"
    with open(creatures_file, 'w', encoding='utf-8') as f:
        json.dump(creatures, f, indent=2, ensure_ascii=False)
    
    # Write traits
    traits_file = output_dir / "CreatureTrait.json"
    with open(traits_file, 'w', encoding='utf-8') as f:
        json.dump(all_traits, f, indent=2, ensure_ascii=False)
    
    # Write actions
    actions_file = output_dir / "CreatureAction.json"
    with open(actions_file, 'w', encoding='utf-8') as f:
        json.dump(all_actions, f, indent=2, ensure_ascii=False)
    
    # Write attacks
    attacks_file = output_dir / "CreatureActionAttack.json"
    with open(attacks_file, 'w', encoding='utf-8') as f:
        json.dump(all_attacks, f, indent=2, ensure_ascii=False)
    
    print(f"\nConversion completed!")
    print(f"Converted {len(creatures)} creatures")
    print(f"Generated {len(all_traits)} traits")
    print(f"Generated {len(all_actions)} actions")
    print(f"Generated {len(all_attacks)} attacks")
    print(f"Files written to {output_dir}")

if __name__ == "__main__":
    main() 