import os
import json
import glob
import re


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r'[^a-z0-9]+', '-', value)
    value = re.sub(r'-+', '-', value)
    return value.strip('-')


def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
        f.write('\n')

def build_doc_mappings():
    v1_to_v2 = {}
    for dpath in glob.glob('data/v1/*/Document.json'):
        doc = load_json(dpath)[0]
        slug = doc['fields']['slug']
        key = doc['fields'].get('v2_related_key', slug)
        v1_to_v2[slug] = key

    v2_paths = {}
    for dpath in glob.glob('data/v2/*/*/Document.json'):
        doc = load_json(dpath)[0]
        doc_key = doc['pk']
        v2_paths[doc_key] = os.path.dirname(dpath)
    return v1_to_v2, v2_paths


def convert_archetype_file(v1_path: str, v2_path: str, doc_key: str):
    if not os.path.exists(v1_path):
        return False

    objs = load_json(v1_path)
    if os.path.exists(v2_path):
        v2_objs = load_json(v2_path)
    else:
        v2_objs = []

    existing = {obj['pk'] for obj in v2_objs}

    for obj in objs:
        slug = obj['pk']
        fields = obj['fields']
        new_pk = f"{doc_key}_{slug}"
        if new_pk in existing:
            continue
        new_fields = {
            'name': fields['name'],
            'desc': fields['desc'],
            'document': doc_key,
            'subclass_of': f"srd_{slugify(fields['char_class'])}",
            'hit_dice': None,
            'caster_type': None,
            'saving_throws': []
        }
        v2_objs.append({'model': 'api_v2.characterclass', 'pk': new_pk, 'fields': new_fields})
        existing.add(new_pk)

    v2_objs.sort(key=lambda x: x['pk'])
    os.makedirs(os.path.dirname(v2_path), exist_ok=True)
    save_json(v2_path, v2_objs)
    return True


def main():
    v1_to_v2, v2_paths = build_doc_mappings()
    for slug, doc_key in v1_to_v2.items():
        v1_file = os.path.join('data', 'v1', slug, 'Archetype.json')
        if not os.path.exists(v1_file):
            continue
        out_dir = v2_paths.get(doc_key)
        if not out_dir:
            continue
        v2_file = os.path.join(out_dir, 'CharacterClass.json')
        if convert_archetype_file(v1_file, v2_file, doc_key):
            print(f'Converted {v1_file} -> {v2_file}')

if __name__ == '__main__':
    main()
