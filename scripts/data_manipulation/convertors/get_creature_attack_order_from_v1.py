"""
W.R.T. https://github.com/open5e/open5e-api/issues/667

This script was writen to migrate the order that actions appear in monster 
stat-blocks from V1 (where they were preserved using their position in a MD
string) to V2 (where there now exists a )

This script is designed to be run once to migrate the existing data. It has 
already been run on our data. It is not included in any build steps. I have
included it here as part of my PR as A) documentation for how this issue was 
resolved, and B) it might be useful to other developer.

But really, all it is doing right now is sitting here, likely gathering dust.
It can be safely deleted.

Calum, Apr 2025
"""

import json
import re

def parse_json(path):
  """Loads JSON data from a file at the given path"""
  if not path:
    return
  with open(path, 'r') as file:
    data = json.load(file)
  return data

def write_json_file(path, data):
  """Writes JSON data to a file"""
  with open(path, 'w') as file:
    json.dump(data, file, indent=2)

def slugify(input):
  """
  Converts an input string to kebab-case. Used to  generate primary keys 
  from monster names.
  """   
  output = input.lower() # convert to lowercase
  output = output.replace(" ", "-")  # replace spaces with hyphens
  output = re.sub(r'[^a-z0-9-]', '', output) # rmv non-alphanumerics
  return output

def extract_action_order(monster, action_key, action_type):
  """
  Extracts action order data from monster for a given action type.

  `action_key` is the name of the field this type of action is stored under
    in the V1 dataset
  `action_type` is the field on a V2 CreatureAction to indicate what type of
    action a given item is ('ACTION', 'BONUS ACTION', etc.)
  """
  action_order_data = []

  # convert monster actions to JSON, inc. null guards
  raw_json = monster.get('fields', {}).get(action_key)
  parsed_actions = json.loads(raw_json or "null")

  # iterate over actions and extract order data
  if parsed_actions:
    for index, action in enumerate(parsed_actions):
      action_order_data.append({
        "name": action['name'],
        "parent": None,  # Parent will be added later
        "order": index,
        "type": action_type
      })
  return action_order_data


def apply_action_orders(output_actions, order_stores):
  """
  applies order numbers to output actions using data from input order stores
  """
  for action in output_actions:
    parent_pk = action['fields']['parent']
    name = action['fields']['name']
    action_type = action['fields']['action_type']

    store = order_stores.get(action_type, {})

    if parent_pk not in store:
      continue

    for original in store[parent_pk]:
      # Ignore text inside parentheses for comparison
      if original['name'].split(' (')[0] == name:
        action['fields']['order'] = original['order']
        break

def generate_v2_pk(monster, document_key):
  """ formats API V2 pk from monster's name and document source key """
  old_name = monster['fields']['name']
  return "{}_{}".format(document_key,slugify(old_name))

def main():
  for source in source_map:
    input_path = source.get('input_path')
    output_path = source.get("output_path")
    v2_doc_key = source.get("v2_document_key")
  
    # import input/output json
    input_json = parse_json(input_path)
    output_json = parse_json(output_path)
    
    # store maping of Monster PK to action ordering infomation
    order_stores = {
      "ACTION": {},
      "BONUS_ACTION": {},
      "LEGENDARY_ACTION": {},
      "REACTION": {}
    }

    # Process each monster to extract ordering info
    for monster in input_json:
        v2_pk = generate_v2_pk(monster, v2_doc_key)

        for key, action_type in [
            ('actions_json', "ACTION"),
            ('bonus_actions_json', "BONUS_ACTION"),
            ('legendary_actions_json', "LEGENDARY_ACTION"),
            ('reactions_json', "REACTION"),
        ]:
            action_data = extract_action_order(monster, key, action_type)
            for a in action_data:
                a['parent'] = v2_pk
            order_stores[action_type][v2_pk] = action_data
    
    # Apply order numbers to the output actions
    apply_action_orders(output_json, order_stores)

    # Write modified output JSON
    write_json_file(output_path, output_json)

# map of input/output files to process
source_map = [
  {
    'v2_document_key': 'srd',
    'input_path': '../../../data/v1/wotc-srd/Monster.json',
    'output_path': '../../../data/v2/wizards-of-the-coast/srd/CreatureAction.json',
  },
  {
    'v2_document_key': 'tob',
    'input_path': '../../../data/v1/tob/Monster.json',
    'output_path': '../../../data/v2/kobold-press/tob/CreatureAction.json',
  },
  {
    'v2_document_key': 'tob-2023',
    'input_path': '../../../data/v1/tob-2023/Monster.json',
    'output_path': '../../../data/v2/kobold-press/tob-2023/CreatureAction.json',
  },
  {
    'v2_document_key': 'tob2',
    'input_path': '../../../data/v1/tob2/Monster.json',
    'output_path': '../../../data/v2/kobold-press/tob2/CreatureAction.json',
  },
  {
    'v2_document_key': 'tob3',
    'input_path': '../../../data/v1/tob3/Monster.json',
    'output_path': '../../../data/v2/kobold-press/tob3/CreatureAction.json',
  },
  {
    'v2_document_key': 'a5e-mm',
    'input_path': '../../../data/v1/menagerie/Monster.json',
    'output_path': '../../../data/v2/en-publishing/a5e-mm/CreatureAction.json',
  },
  {
    'v2_document_key': 'ccdx',
    'input_path': '../../../data/v1/cc/Monster.json',
    'output_path': '../../../data/v2/kobold-press/ccdx/CreatureAction.json',
  },
  {
    'v2_document_key': 'tdcs',
    'input_path': '../../../data/v1/taldorei/Monster.json',
    'output_path': '../../../data/v2/green-ronin/tdcs/CreatureAction.json',
  },
  {
    'v2_document_key': 'bfrd',
    'input_path': '../../../data/v1/blackflag/Monster.json',
    'output_path': '../../../data/v2/kobold-press/bfrd/CreatureAction.json',
  },
]

if __name__ == "__main__":
  main()