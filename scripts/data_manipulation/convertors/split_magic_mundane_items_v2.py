"""
This script was authored when attempt to split the Item model into Item and
MagicItem sub-models.
"""

import json

INPUT_FILE = "
MUNDANE_OUTPUT_FILE = "Item.json"
MAGIC_OUTPUT_FILE = "MagicItem.json"

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    items = json.load(f)

mundane_items = []
magic_items = []

for item in items:
    fields = item.get("fields", {})
    rarity = fields.get("rarity")

    if rarity is not None:
        item["model"] = "api_v2.magicitem"
        magic_items.append(item)
    else:
        for key in ("rarity", "requires_attunement", "attunement_detail"):
            fields.pop(key, None)
        mundane_items.append(item)

with open(MUNDANE_OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(mundane_items, f, indent=2, ensure_ascii=False)

with open(MAGIC_OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(magic_items, f, indent=2, ensure_ascii=False)