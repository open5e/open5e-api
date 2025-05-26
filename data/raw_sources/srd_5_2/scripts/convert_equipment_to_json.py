#!/usr/bin/env python3
"""
Convert SRD 5.2 Equipment to JSON format for Open5e API v2
"""

import json
import re
from pathlib import Path

def load_srd_document():
    """Load the SRD 5.2 markdown file"""
    script_dir = Path(__file__).parent
    srd_path = script_dir.parent / "DND-SRD-5.2-CC.md"
    with open(srd_path, 'r', encoding='utf-8') as f:
        return f.read()

def parse_adventuring_gear(content):
    """Parse adventuring gear from the SRD content"""
    gear_list = []
    
    # Find the adventuring gear table
    gear_match = re.search(r'Table: Adventuring Gear\s*\n\s*\|(.*?)\n\n', content, re.DOTALL)
    if not gear_match:
        print("Could not find adventuring gear table")
        return gear_list
    
    lines = gear_match.group(1).strip().split('\n')
    
    for line in lines[2:]:  # Skip header and separator
        if not line.strip() or line.startswith('|---'):
            continue
            
        parts = [p.strip() for p in line.split('|')[1:-1]]  # Remove empty first/last
        if len(parts) < 3:
            continue
        
        name = parts[0].strip()
        weight_text = parts[1].strip()
        cost_text = parts[2].strip()
        
        if not name or name == '—':
            continue
        
        # Parse weight
        weight = 0.0
        if weight_text and weight_text != '—':
            weight_match = re.search(r'([\d.]+)', weight_text)
            if weight_match:
                weight = float(weight_match.group(1))
        
        # Parse cost
        cost = 0.0
        if cost_text and cost_text != 'Varies':
            # Convert to GP
            if 'GP' in cost_text:
                cost_match = re.search(r'([\d,]+)', cost_text.replace(',', ''))
                if cost_match:
                    cost = float(cost_match.group(1))
            elif 'SP' in cost_text:
                cost_match = re.search(r'([\d.]+)', cost_text)
                if cost_match:
                    cost = float(cost_match.group(1)) / 10
            elif 'CP' in cost_text:
                cost_match = re.search(r'([\d.]+)', cost_text)
                if cost_match:
                    cost = float(cost_match.group(1)) / 100
        
        gear_list.append({
            'name': name,
            'weight': weight,
            'cost': cost,
            'desc': f"A {name.lower()}."
        })
    
    return gear_list

def parse_tools(content):
    """Parse tools from the SRD content"""
    tools_list = []
    
    # Find the Artisan's Tools section
    artisan_match = re.search(r'### Artisan\'s Tools\s*\n(.*?)(?=\n### |\Z)', content, re.DOTALL)
    if artisan_match:
        artisan_text = artisan_match.group(1)
        
        # Parse individual artisan tools
        tool_pattern = r'#### ([^(]+)\(([^)]+)\)'
        tool_matches = re.findall(tool_pattern, artisan_text)
        
        for name, cost_text in tool_matches:
            name = name.strip()
            cost_text = cost_text.strip()
            
            # Parse cost
            cost = 0.0
            if 'GP' in cost_text:
                cost_match = re.search(r'([\d,]+)', cost_text.replace(',', ''))
                if cost_match:
                    cost = float(cost_match.group(1))
            elif 'SP' in cost_text:
                cost_match = re.search(r'([\d.]+)', cost_text)
                if cost_match:
                    cost = float(cost_match.group(1)) / 10
            
            tools_list.append({
                'name': name,
                'cost': cost,
                'category': 'Artisan\'s Tools',
                'desc': f"A {name.lower()} tool."
            })
    
    # Find the Other Tools section
    other_match = re.search(r'### Other Tools\s*\n(.*?)(?=\n## |\Z)', content, re.DOTALL)
    if other_match:
        other_text = other_match.group(1)
        
        # Parse individual other tools
        tool_pattern = r'#### ([^(]+)\(([^)]+)\)'
        tool_matches = re.findall(tool_pattern, other_text)
        
        for name, cost_text in tool_matches:
            name = name.strip()
            cost_text = cost_text.strip()
            
            # Skip variants entries
            if 'Varies' in cost_text:
                continue
            
            # Parse cost
            cost = 0.0
            if 'GP' in cost_text:
                cost_match = re.search(r'([\d,]+)', cost_text.replace(',', ''))
                if cost_match:
                    cost = float(cost_match.group(1))
            elif 'SP' in cost_text:
                cost_match = re.search(r'([\d.]+)', cost_text)
                if cost_match:
                    cost = float(cost_match.group(1)) / 10
            
            tools_list.append({
                'name': name,
                'cost': cost,
                'category': 'Other Tools',
                'desc': f"A {name.lower()} tool."
            })
    
    # Parse Gaming Set and Musical Instrument variants
    gaming_variants = [
        ('Dice', 0.1),  # 1 SP = 0.1 GP
        ('Dragonchess', 1.0),
        ('Playing Cards', 0.5),  # 5 SP = 0.5 GP
        ('Three-Dragon Ante', 1.0)
    ]
    
    for name, cost in gaming_variants:
        tools_list.append({
            'name': name,
            'cost': cost,
            'category': 'Gaming Sets',
            'desc': f"A {name.lower()} gaming set."
        })
    
    musical_variants = [
        ('Bagpipes', 30.0),
        ('Drum', 6.0),
        ('Dulcimer', 25.0),
        ('Flute', 2.0),
        ('Horn', 3.0),
        ('Lute', 35.0),
        ('Lyre', 30.0),
        ('Pan Flute', 12.0),
        ('Shawm', 2.0),
        ('Viol', 30.0)
    ]
    
    for name, cost in musical_variants:
        tools_list.append({
            'name': name,
            'cost': cost,
            'category': 'Musical Instruments',
            'desc': f"A {name.lower()} musical instrument."
        })
    
    return tools_list

def create_items_json(gear_data, tools_data):
    """Create Item JSON objects for all equipment"""
    items_json = []
    
    # Adventuring gear items
    for gear in gear_data:
        key = f"srd2024_{gear['name'].lower().replace(' ', '-').replace(',', '').replace('(', '').replace(')', '').replace(chr(39), '')}"
        
        items_json.append({
            "model": "api_v2.item",
            "pk": key,
            "fields": {
                "name": gear['name'],
                "desc": gear['desc'],
                "document": "srd-2024",
                "size": "tiny",
                "weight": f"{gear['weight']:.3f}",
                "armor_class": 0,
                "hit_points": 0,
                "hit_dice": None,
                "nonmagical_attack_resistance": False,
                "nonmagical_attack_immunity": False,
                "cost": f"{gear['cost']:.2f}" if gear['cost'] > 0 else None,
                "weapon": None,
                "armor": None,
                "category": "adventuring-gear",
                "requires_attunement": False,
                "rarity": None,
                "damage_vulnerabilities": [],
                "damage_immunities": [
                    "poison",
                    "psychic"
                ],
                "damage_resistances": []
            }
        })
    
    # Tool items
    for tool in tools_data:
        key = f"srd2024_{tool['name'].lower().replace(' ', '-').replace(',', '').replace('(', '').replace(')', '').replace(chr(39), '').replace('*', '')}"
        
        items_json.append({
            "model": "api_v2.item",
            "pk": key,
            "fields": {
                "name": tool['name'],
                "desc": tool['desc'],
                "document": "srd-2024",
                "size": "tiny",
                "weight": "1.000",
                "armor_class": 0,
                "hit_points": 0,
                "hit_dice": None,
                "nonmagical_attack_resistance": False,
                "nonmagical_attack_immunity": False,
                "cost": f"{tool['cost']:.2f}" if tool['cost'] > 0 else None,
                "weapon": None,
                "armor": None,
                "category": "tools",
                "requires_attunement": False,
                "rarity": None,
                "damage_vulnerabilities": [],
                "damage_immunities": [
                    "poison",
                    "psychic"
                ],
                "damage_resistances": []
            }
        })
    
    return items_json

def create_item_categories():
    """Create ItemCategory JSON objects"""
    categories = [
        {
            "model": "api_v2.itemcategory",
            "pk": "adventuring-gear",
            "fields": {
                "name": "Adventuring Gear",
                "document": "srd-2024"
            }
        },
        {
            "model": "api_v2.itemcategory",
            "pk": "tools",
            "fields": {
                "name": "Tools",
                "document": "srd-2024"
            }
        }
    ]
    return categories



def main():
    print("Converting SRD 5.2 Equipment to JSON format...")
    
    # Load the SRD document
    content = load_srd_document()
    
    # Parse equipment types
    print("\nParsing adventuring gear...")
    gear_data = parse_adventuring_gear(content)
    print(f"Found {len(gear_data)} adventuring gear items")
    
    print("\nParsing tools...")
    tools_data = parse_tools(content)
    print(f"Found {len(tools_data)} tools")
    
    # Convert to JSON format
    print("\nConverting to JSON format...")
    items_json = create_items_json(gear_data, tools_data)
    categories_json = create_item_categories()
    
    # Write JSON files
    output_dir = Path("../../../v2/wizards-of-the-coast/srd-2024/")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\nWriting JSON files to {output_dir}...")
    
    # Write ItemCategory.json
    categories_file = output_dir / "ItemCategory.json"
    with open(categories_file, 'w', encoding='utf-8') as f:
        json.dump(categories_json, f, indent=2, ensure_ascii=False)
    
    # Check if Item.json already exists and merge
    items_file = output_dir / "Item.json"
    existing_items = []
    
    if items_file.exists():
        with open(items_file, 'r', encoding='utf-8') as f:
            existing_items = json.load(f)
        print(f"Found {len(existing_items)} existing items - will overwrite with new format")
    
    # Write new items (overwrite existing file)
    with open(items_file, 'w', encoding='utf-8') as f:
        json.dump(items_json, f, indent=2, ensure_ascii=False)
    
    print(f"\nConversion complete!")
    print(f"- Created {len(categories_json)} item categories")
    print(f"- Created {len(items_json)} new items")
    print(f"\nFiles written to {output_dir}")
    print(f"\nTo import, run: python manage.py quicksetup --clean")

if __name__ == "__main__":
    main() 