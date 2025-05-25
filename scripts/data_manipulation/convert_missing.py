import json, os
from django.template.defaultfilters import slugify

# Map v1 document ids to v2 slugs
DOC_MAP = {}
for path in [
    "data/v1/toh/Document.json",
    "data/v1/taldorei/Document.json",
    "data/v1/o5e/Document.json",
]:
    obj = json.load(open(path))
    for item in obj:
        DOC_MAP[item["pk"]] = item["fields"].get("v2_related_key", item["fields"].get("slug"))

def load_json(path):
    return json.load(open(path)) if os.path.exists(path) else []

def save_json(data, path):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def append_json(data, path):
    cur = load_json(path)
    cur.extend(data)
    save_json(cur, path)

def convert_feats(v1_path, out_dir, doc_slug, start_pk):
    feats_v1 = load_json(v1_path)
    feats_v2 = []
    fb_v2 = []
    pk_counter = start_pk
    for feat in feats_v1:
        f = feat["fields"]
        slug = feat["pk"]
        pk = f"{doc_slug}_{slug}"
        feats_v2.append({
            "model": "api_v2.feat",
            "pk": pk,
            "fields": {
                "name": f["name"],
                "desc": f["desc"],
                "prerequisite": f.get("prerequisite"),
                "document": doc_slug,
            },
        })
        eff = f.get("effects_desc_json")
        if eff:
            try:
                parts = json.loads(eff)
            except Exception:
                parts = []
            for part in parts:
                fb_v2.append({
                    "model": "api_v2.featbenefit",
                    "pk": pk_counter,
                    "fields": {"name": "", "desc": part, "type": None, "parent": pk},
                })
                pk_counter += 1
    if feats_v2:
        save_json(feats_v2, os.path.join(out_dir, "Feat.json"))
    if fb_v2:
        save_json(fb_v2, os.path.join(out_dir, "FeatBenefit.json"))
    return pk_counter

def convert_species_add(species_path, item_fields, pk_prefix, parent=None):
    data = load_json(species_path)
    data.append({
        "model": "api_v2.species",
        "pk": f"{pk_prefix}_{slugify(item_fields['name'])}",
        "fields": {
            "name": item_fields["name"],
            "desc": item_fields["desc"],
            "document": pk_prefix,
            "subspecies_of": parent,
        },
    })
    save_json(data, species_path)

def convert_subclasses(v1_path, out_dir, doc_slug):
    data_v1 = load_json(v1_path)
    out = []
    for obj in data_v1:
        f = obj["fields"]
        slug = obj["pk"]
        base = slugify(f["char_class"])
        out.append({
            "model": "api_v2.characterclass",
            "pk": f"{doc_slug}_{slug}",
            "fields": {
                "name": f["name"],
                "document": doc_slug,
                "subclass_of": f"srd_{base}",
                "hit_dice": None,
                "caster_type": None,
                "saving_throws": [],
            },
        })
    if out:
        save_json(out, os.path.join(out_dir, "CharacterClass.json"))

def convert_backgrounds(v1_path, out_dir, doc_slug):
    bgs = load_json(v1_path)
    out_bg = []
    out_bgb = []
    for bg in bgs:
        f = bg["fields"]
        slug = bg["pk"]
        pk = f"{doc_slug}_{slug}"
        out_bg.append({
            "model": "api_v2.background",
            "pk": pk,
            "fields": {"name": f["name"], "desc": f["desc"], "document": doc_slug},
        })
        mapping = [
            ("skill_proficiencies", "Skill Proficiencies", "skill_proficiency"),
            ("tool_proficiencies", "Tool Proficiencies", "tool_proficiency"),
            ("languages", "Languages", "language"),
            ("equipment", "Equipment", "equipment"),
        ]
        for key, name, typ in mapping:
            val = f.get(key)
            if val:
                out_bgb.append({
                    "model": "api_v2.backgroundbenefit",
                    "pk": f"{pk}_{slugify(name)}",
                    "fields": {"name": name, "desc": val, "type": typ, "parent": pk},
                })
        if f.get("feature") or f.get("feature_desc"):
            out_bgb.append({
                "model": "api_v2.backgroundbenefit",
                "pk": f"{pk}_{slugify(f.get('feature','feature'))}",
                "fields": {"name": f.get("feature", "Feature"), "desc": f.get("feature_desc", ""), "type": "feature", "parent": pk},
            })
        if f.get("suggested_characteristics"):
            out_bgb.append({
                "model": "api_v2.backgroundbenefit",
                "pk": f"{pk}_suggested-characteristics",
                "fields": {"name": "Suggested Characteristics", "desc": f["suggested_characteristics"], "type": "suggested_characteristics", "parent": pk},
            })
    if out_bg:
        save_json(out_bg, os.path.join(out_dir, "Background.json"))
    if out_bgb:
        save_json(out_bgb, os.path.join(out_dir, "BackgroundBenefit.json"))

import re

def parse_feature_sections(text):
    sections = []
    parts = text.split("##### ")
    for part in parts[1:]:
        if not part.strip():
            continue
        header, *rest = part.split("\n", 1)
        body = rest[0] if rest else ""
        sections.append((header.strip(), body.strip()))
    return sections

def extract_level(desc):
    match = re.search(r"(\d+)(?:st|nd|rd|th) level", desc, re.IGNORECASE)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None

def convert_archetype_features(v1_path, out_dir, doc_slug):
    data = load_json(v1_path)
    features = []
    items = []
    for obj in data:
        slug = obj["pk"]
        parent = f"{doc_slug}_{slug}"
        sections = parse_feature_sections(obj["fields"].get("desc", ""))
        for name, desc in sections:
            feat_slug = f"{parent}_{slugify(name)}"
            features.append({
                "model": "api_v2.classfeature",
                "pk": feat_slug,
                "fields": {
                    "name": name,
                    "desc": desc,
                    "document": doc_slug,
                    "parent": parent,
                },
            })
            level = extract_level(desc)
            if level:
                items.append({
                    "model": "api_v2.classfeatureitem",
                    "pk": f"{feat_slug}_{level}",
                    "fields": {"parent": feat_slug, "level": level, "column_value": None},
                })
    if features:
        save_json(features, os.path.join(out_dir, "ClassFeature.json"))
    if items:
        save_json(items, os.path.join(out_dir, "ClassFeatureItem.json"))

def convert_species_traits(subrace_path, out_path, parent_slug, start_pk):
    subrace = load_json(subrace_path)[0]
    fields = subrace["fields"]
    traits = []
    pk = start_pk
    asi = fields.get("asi_desc")
    if asi:
        traits.append({
            "model": "api_v2.speciestrait",
            "pk": pk,
            "fields": {"name": "Ability Score Increase", "desc": asi, "type": None, "parent": parent_slug},
        })
        pk += 1
    text = fields.get("traits", "")
    for part in filter(None, [p.strip() for p in text.split("\n\n")]):
        m = re.match(r"\*\*[_*]?([^.*]+)[.*_]*\*\*\s*(.*)", part)
        if m:
            name = m.group(1).strip().rstrip('.')
            desc = m.group(2).strip()
        else:
            name, _, desc = part.partition('.')
            name = name.strip()
            desc = desc.strip()
        traits.append({
            "model": "api_v2.speciestrait",
            "pk": pk,
            "fields": {"name": name, "desc": desc, "type": None, "parent": parent_slug},
        })
        pk += 1
    append_json(traits, out_path)
    return pk

if __name__ == "__main__":
    pk_counter = 240
    pk_counter = convert_feats("data/v1/toh/Feat.json", "data/v2/kobold-press/toh", "toh", pk_counter)
    pk_counter = convert_feats("data/v1/taldorei/Feat.json", "data/v2/green-ronin/tdcs", "tdcs", pk_counter)

    races = load_json("data/v1/toh/Race.json")
    shade = next(r for r in races if r["fields"]["name"] == "Shade")
    convert_species_add("data/v2/kobold-press/toh/Species.json", shade["fields"], "toh", None)

    subrace = load_json("data/v1/o5e/Subrace.json")[0]
    convert_species_add("data/v2/open5e/open5e/Species.json", subrace["fields"], "open5e", "srd_halfling")

    convert_backgrounds("data/v1/o5e/Background.json", "data/v2/open5e/open5e", "open5e")

    convert_subclasses("data/v1/o5e/Archetype.json", "data/v2/open5e/open5e", "open5e")
    convert_subclasses("data/v1/toh/Archetype.json", "data/v2/kobold-press/toh", "toh")
    convert_subclasses("data/v1/taldorei/Archetype.json", "data/v2/green-ronin/tdcs", "tdcs")

    convert_archetype_features("data/v1/o5e/Archetype.json", "data/v2/open5e/open5e", "open5e")
    convert_archetype_features("data/v1/toh/Archetype.json", "data/v2/kobold-press/toh", "toh")
    convert_archetype_features("data/v1/taldorei/Archetype.json", "data/v2/green-ronin/tdcs", "tdcs")

    pk_counter = convert_species_traits(
        "data/v1/o5e/Subrace.json",
        "data/v2/open5e/open5e/SpeciesTrait.json",
        "open5e_stoor-halfling",
        286,
    )
