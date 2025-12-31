# Spell Validation

## Validating "At Higher Levels" Casting Options

All spells that have "At Higher Levels" descriptions in their `higher_level` field should have corresponding `SpellCastingOption` entries that define the specific changes when the spell is cast at higher levels.

### Running the Validation

To check that all spells with "At Higher Levels" text have the required casting options, run:

```bash
pipenv run python manage.py validate_spell_higher_levels
```

This will check all v2 spell data by default. You can specify a specific directory:

```bash
pipenv run python manage.py validate_spell_higher_levels -d data/v2/wizards-of-the-coast/srd-2024
```

### Expected Output

If all spells are properly configured:
```
Validation complete:
  Total spells checked: 338
  ✓ All spells with "higher_level" text have casting options!
```

If spells are missing casting options:
```
data/v2/wizards-of-the-coast/srd-2024/Spell.json:
  ✗ Aid (level 2, pk: srd-2024_aid)
    Higher Level: Each target's Hit Points increase by 5 for each spell slot level above 2.

Validation complete:
  Total spells checked: 338
  ✗ 1 spell(s) missing casting options
```

### Adding Missing Casting Options

When the validation identifies missing casting options, you need to:

1. Create `SpellCastingOption` entries in the corresponding `SpellCastingOption.json` file
2. Follow the existing pattern for similar spells
3. Key fields to populate:
   - `parent`: The spell's primary key
   - `type`: The casting option type (e.g., `slot_level_3`, `player_level_5`)
   - `damage_roll`, `target_count`, `duration`, `range`, `concentration`, `shape_size`: Specific changes for this casting level
   - `desc`: Description of complex effects that can't be captured in other fields

### Example SpellCastingOption Entry

```json
{
  "model": "api_v2.spellcastingoption",
  "pk": 10585,
  "fields": {
    "parent": "srd-2024_aid",
    "type": "slot_level_3",
    "damage_roll": null,
    "target_count": null,
    "duration": null,
    "range": null,
    "concentration": null,
    "shape_size": null,
    "desc": "Each target's Hit Points increase by 10"
  }
}
```

### When to Run

- **Before committing new spell data**: Always validate to ensure no casting options are missed
- **As part of code review**: Reviewers can run this to verify spell data is complete
- **During development**: When working with spell data to catch issues early

### Related Files

- Validation command: `api_v2/management/commands/validate_spell_higher_levels.py`
- Spell model: `api_v2/models/spell.py`
- Spell data: `data/v2/*/Spell.json`
- Casting options: `data/v2/*/SpellCastingOption.json`
