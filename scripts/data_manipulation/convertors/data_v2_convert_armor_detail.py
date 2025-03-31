"""
  This script was written to address issue #300 - it migrates the  'armor_desc'
  field in our v1 monster data to the 'armor_detail' in our v2 creature data.
"""


import json
import re

def parse_json(path):
  if not path:
    return
  with open(path, 'r') as file:
    data = json.load(file)
  return data

def write_json_file(path, data):
  with open(path, 'w') as file:
    json.dump(data, file, indent=2)

def slugify(input):
    """
      Converts an input string to slugified camel-case. Here, it is used to 
      help generate primary keys from monster names.
    """   
    output = input.lower() # convert to lowercase
    output = output.replace(" ", "-")  # replace spaces with hyphens
    output = re.sub(r'[^a-z0-9-]', '', output) # rmv non-alphanumerics
    return output

def get_v2_pk(monster, document_key):
  """ Formats API V2 pk from monster's name and document source key """
  old_name = monster['fields']['name']
  return "{}_{}".format(document_key,slugify(old_name))
  

def main():
    # iterate over specified sources
    for source in source_map:
      input_path = source.get("input_path")
      output_path = source.get("output_path")
      v2_doc_key = source.get("v2_document_key")

      # import json
      input_json = parse_json(input_path)
      output_json = parse_json(output_path)

      # dictionary for temporarily storing 'armor_detail' data
      armor_detail_store = {}

      # get armor_detail for v1 data, store in dict
      for monster in input_json:
        new_key = get_v2_pk(monster, v2_doc_key)
        armor_detail = monster['fields']['armor_desc']
        armor_detail_store[new_key] = monster['fields']['armor_desc']

      # add armor_detail to v2_data (where applicable)
      for monster in output_json:
        key = monster['pk']
        armor_detail = armor_detail_store.get(key)
        if armor_detail:
          monster['fields']['armor_detail'] = armor_detail
      
      # write updated json to v2 data
      write_json_file(output_path, output_json)

# a list sources to convert
source_map = [
  {
    'v2_document_key': 'srd',
    'input_path': '../../../data/v1/wotc-srd/Monster.json',
    'output_path': '../../../data/v2/wizards-of-the-coast/srd/Creature.json',
  },
  {
    'v2_document_key': 'tob',
    'input_path': '../../../data/v1/tob/Monster.json',
    'output_path': '../../../data/v2/kobold-press/tob/Creature.json',
  },
  {
    'v2_document_key': 'tob-2023',
    'input_path': '../../../data/v1/tob-2023/Monster.json',
    'output_path': '../../../data/v2/kobold-press/tob-2023/Creature.json',
  },
  {
    'v2_document_key': 'tob2',
    'input_path': '../../../data/v1/tob2/Monster.json',
    'output_path': '../../../data/v2/kobold-press/tob2/Creature.json',
  },
  {
    'v2_document_key': 'tob3',
    'input_path': '../../../data/v1/tob3/Monster.json',
    'output_path': '../../../data/v2/kobold-press/tob3/Creature.json',
  },
  {
    'v2_document_key': 'mmenag',
    'input_path': '../../../data/v1/menagerie/Monster.json',
    'output_path': '../../../data/v2/en-publishing/mmenag/Creature.json',
  },
  {
    'v2_document_key': 'ccdx',
    'input_path': '../../../data/v1/cc/Monster.json',
    'output_path': '../../../data/v2/kobold-press/ccdx/Creature.json',
  },
  {
    'v2_document_key': 'tdcs',
    'input_path': '../../../data/v1/taldorei/Monster.json',
    'output_path': '../../../data/v2/green-ronin/tdcs/Creature.json',
  },
  {
    'v2_document_key': 'bfrd',
    'input_path': '../../../data/v1/blackflag/Monster.json',
    'output_path': '../../../data/v2/kobold-press/bfrd/Creature.json',
  },
]


if __name__ == "__main__":
  main()