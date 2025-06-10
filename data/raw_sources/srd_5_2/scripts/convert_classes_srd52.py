#!/usr/bin/env python3
"""
SRD 5.2 Character Class Generator

This script creates basic character class data for SRD 2024 classes
that are referenced by the spells. This provides the minimal class
data needed to satisfy foreign key constraints.
"""

import json
from pathlib import Path
from typing import Dict, List, Any

def create_basic_classes() -> List[Dict[str, Any]]:
    """Create basic character class data for SRD 2024."""
    
    # Basic class data - minimal information needed for spell references
    classes_data = [
        {
            "name": "Bard", 
            "hit_dice": "D8",
            "caster_type": "FULL",
            "saving_throws": ["cha", "dex"]
        },
        {
            "name": "Cleric",
            "hit_dice": "D8", 
            "caster_type": "FULL",
            "saving_throws": ["cha", "wis"]
        },
        {
            "name": "Druid",
            "hit_dice": "D8",
            "caster_type": "FULL", 
            "saving_throws": ["int", "wis"]
        },
        {
            "name": "Fighter",
            "hit_dice": "D12",
            "caster_type": "NONE", 
            "saving_throws": ["str", "con"]
        },
        {
            "name": "Barbarian",
            "hit_dice": "D12",
            "caster_type": "NONE", 
            "saving_throws": ["str", "con"]
        },
        {
            "name": "Monk",
            "hit_dice": "D8",
            "caster_type": "NONE", 
            "saving_throws": ["str", "dex"]
        },

        {
            "name": "Paladin",
            "hit_dice": "D10",
            "caster_type": "HALF",
            "saving_throws": ["cha", "wis"]
        },
        {
            "name": "Ranger",
            "hit_dice": "D10",
            "caster_type": "HALF",
            "saving_throws": ["dex", "str"]
        },
        {
            "name": "Sorcerer",
            "hit_dice": "D6",
            "caster_type": "FULL",
            "saving_throws": ["cha", "con"]
        },
        {
            "name": "Warlock",
            "hit_dice": "D8",
            "caster_type": "PACT",
            "saving_throws": ["cha", "wis"]
        },
        {
            "name": "Wizard",
            "hit_dice": "D6",
            "caster_type": "FULL",
            "saving_throws": ["int", "wis"]
        }
    ]
    
    # Convert to Django fixture format
    fixtures = []
    for class_data in classes_data:
        # Create primary key
        pk = f"srd-2024_{class_data['name'].lower()}"
        
        fixture = {
            "model": "api_v2.characterclass",
            "pk": pk,
            "fields": {
                "name": class_data["name"],
                "document": "srd-2024",
                "subclass_of": None,
                "hit_dice": class_data["hit_dice"],
                "caster_type": class_data["caster_type"],
                "saving_throws": class_data["saving_throws"]
            }
        }
        fixtures.append(fixture)
    
    return fixtures

def main():
    """Main function to generate character class data."""
    output_file = Path("../../../v2/wizards-of-the-coast/srd-2024/CharacterClass.json")
    
    print(f"Generating SRD 2024 character classes...")
    
    # Create class data
    classes = create_basic_classes()
    
    # Write to file
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(classes, f, indent=2, ensure_ascii=False)
    
    print(f"Generated {len(classes)} character classes")
    print(f"Classes written to {output_file}")

if __name__ == "__main__":
    main() 