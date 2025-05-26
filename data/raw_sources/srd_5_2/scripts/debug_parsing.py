#!/usr/bin/env python3

import re
from pathlib import Path

def parse_standardized_item(content: str):
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
            key_match = re.match(r'\*\*(.*?)\*\*:\s*(.*)', line)
            if key_match:
                key = key_match.group(1).strip()
                value = key_match.group(2).strip()
                item_data[key] = value
    
    return item_data

def create_property_assignment(weapon_pk: str, property_name: str, detail: str = None):
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

# Test with first weapon
weapons_file = Path('../sections/07_weapons_items.md')
with open(weapons_file, 'r', encoding='utf-8') as f:
    content = f.read()

weapon_sections = re.split(r'\n## ', content)
first_weapon = '## ' + weapon_sections[1]

print("First weapon section lines:")
lines = first_weapon.strip().split('\n')
for i, line in enumerate(lines[:10]):
    print(f"{i}: {repr(line)}")

print("\nTesting regex on each line:")
for line in lines:
    if line.startswith('**'):
        print(f"Line: {repr(line)}")
        if ':**' in line:
            print("  Contains :**")
            key_match = re.match(r'\*\*(.*?)\*\*:\s*(.*)', line)
            if key_match:
                print(f"  Match: key='{key_match.group(1)}', value='{key_match.group(2)}'")
            else:
                print("  No regex match")
        else:
            print("  Does not contain :**")

print("\nParsed data:")
weapon_data = parse_standardized_item(first_weapon)
print(weapon_data)

# Test with first few weapons
weapons_file = Path('../sections/07_weapons_items.md')
with open(weapons_file, 'r', encoding='utf-8') as f:
    content = f.read()

weapon_sections = re.split(r'\n## ', content)

for i, section in enumerate(weapon_sections[1:4]):  # Test first 3 weapons
    section = '## ' + section
    weapon_data = parse_standardized_item(section)
    
    print(f"=== Weapon {i+1} ===")
    print(f"Name: {weapon_data.get('name', 'MISSING')}")
    print(f"Damage: {weapon_data.get('Damage', 'MISSING')}")
    print(f"Properties: {weapon_data.get('Properties', 'MISSING')}")
    print(f"Mastery: {weapon_data.get('Mastery', 'MISSING')}")
    print(f"Range: {weapon_data.get('Range', 'MISSING')}")
    print(f"Long Range: {weapon_data.get('Long Range', 'MISSING')}")
    print()
    
    # Test property assignment creation
    properties_str = weapon_data.get('Properties', '')
    mastery = weapon_data.get('Mastery', '')
    weapon_pk = f"srd2024_{weapon_data.get('name', '').lower().replace(' ', '-')}"
    
    assignments = []
    
    # Standard properties
    if 'Light' in properties_str:
        assignments.append(create_property_assignment(weapon_pk, 'light-wp'))
    if 'Finesse' in properties_str:
        assignments.append(create_property_assignment(weapon_pk, 'finesse-wp'))
    if 'Heavy' in properties_str:
        assignments.append(create_property_assignment(weapon_pk, 'heavy-wp'))
    if 'Reach' in properties_str:
        assignments.append(create_property_assignment(weapon_pk, 'reach-wp'))
    if 'Thrown' in properties_str:
        assignments.append(create_property_assignment(weapon_pk, 'thrown-wp'))
    if 'Two-Handed' in properties_str:
        assignments.append(create_property_assignment(weapon_pk, 'two-handed-wp'))
    if 'Loading' in properties_str:
        assignments.append(create_property_assignment(weapon_pk, 'loading-wp'))
    if 'Ammunition' in properties_str:
        assignments.append(create_property_assignment(weapon_pk, 'ammunition-wp'))
    if 'Versatile' in properties_str:
        versatile_match = re.search(r'Versatile \(([^)]+)\)', properties_str)
        detail = versatile_match.group(1) if versatile_match else None
        assignments.append(create_property_assignment(weapon_pk, 'versatile-wp', detail))
    
    # Mastery property
    if mastery and mastery != '—':
        mastery_lower = mastery.lower()
        assignments.append(create_property_assignment(weapon_pk, f'{mastery_lower}-mastery'))
    
    print(f"Generated {len(assignments)} property assignments:")
    for assignment in assignments:
        print(f"  - {assignment['pk']}: {assignment['fields']['property']}")
    print() 