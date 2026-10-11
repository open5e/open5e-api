# Shared concepts

Some concepts are so universal across 5e that we treat them as "core": basic world concepts that mean the same thing in every game system and document. Charisma, acid damage, and the poisoned condition are the same idea whether they come from the SRD 2014, the SRD 2024, or Level Up Advanced 5e.

Core concepts belong to the `core` document, and their fixtures live in [data/v2/open5e/core](../../data/v2/open5e/core). Their keys are not prefixed with a document key (e.g. `acid`, not `srd-2014_acid`).

The core concepts are:
- Ability (e.g. Strength)
- Alignment (e.g. Chaotic Good)
- Condition (e.g. Poisoned)
- Creature Type (e.g. Aberration)
- Damage Type (e.g. Acid)
- Environment (e.g. Mountains)
- Item Category (e.g. Scroll)
- Item Rarity (e.g. Uncommon)
- Language (e.g. Dwarvish)
- Size (e.g. Large)
- Skill (e.g. Animal Handling)
- Spell School (e.g. Illusion)

## Descriptions

Different documents often describe the same core concept in different words. Rather than pick one, these concepts store their descriptions in a separate model, with one description per document:

| Core model     | Description model          |
|----------------|----------------------------|
| `Ability`      | `AbilityDescription`       |
| `Alignment`    | `AlignmentDescription`     |
| `Condition`    | `ConditionDescription`     |
| `CreatureType` | `CreatureTypeDescription`  |
| `DamageType`   | `DamageTypeDescription`    |
| `Skill`        | `SkillDescription`         |

Each description has a `describes` foreign key to the core object and a `document` foreign key to its source. Its fixture lives in the source document's directory, and its key is prefixed with that document's key. For example, `srd-2024_acid` in [data/v2/wizards-of-the-coast/srd-2024/DamageTypeDescription.json](../../data/v2/wizards-of-the-coast/srd-2024/DamageTypeDescription.json):

```json
{
  "model": "api_v2.damagetypedescription",
  "pk": "srd-2024_acid",
  "fields": {
    "desc": "Corrosive liquids, digestive enzymes",
    "describes": "acid",
    "document": "srd-2024"
  }
}
```

The API returns every description on the core object, each labelled with its document and game system:

```json
{
  "key": "radiant",
  "name": "Radiant",
  "document": "core",
  "descriptions": [
    { "desc": "Radiant damage, dealt by a cleric's ...", "document": "srd-2014", "gamesystem": "5e-2014" },
    { "desc": "Holy energy, searing radiation", "document": "srd-2024", "gamesystem": "5e-2024" }
  ]
}
```

To add descriptions from a new document, add a `<Model>Description.json` file to that document's directory. The core object does not need to change.

The remaining core concepts do not use this pattern yet. Environment, Language and Spell School have a single `desc` field on the core object, and Item Category, Item Rarity and Size have no description.

## Exceptions

When a document adds something that only exists in that document, it belongs to that document rather than to `core`. For example, Level Up Advanced 5e adds conditions such as Bloodied and Rattled. These are `Condition` objects in the `a5e-ag` document (`a5e-ag_bloodied`), with their descriptions alongside them in `a5e-ag`.
