'''
W.R.T. https://github.com/open5e/open5e-api/issues/655

This script was writen to migrate the plain-text descriptions of a creature's 
resistances and immunities from the v1 to v2 data.

This script is designed to be run once to migrate the existing data. It has 
already been run on our data. It is not included in any build steps. I have
included it here as part of my PR as A) documentation for how this issue was 
resolved, and B) it might be useful to other developer.

But really, all it is doing right now is sitting here, likely gathering dust.
It can be safely deleted.

Calum, May 2025
'''

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


def generate_v2_pk(monster, document_key):
  """ formats API V2 pk from monster's name and document source key """
  old_name = monster['fields']['name']
  return "{}_{}".format(document_key,slugify(old_name))



def main():
  for source in source_map:
    input_path = source.get('input_path')
    output_path = source.get('output_path')
    v2_doc_key = source.get('v2_document_key')

    # import input/output json
    input_json = parse_json(input_path)
    output_json = parse_json(output_path)

    resistances_and_immunities_storage = {}

    # iterate over creatures in input
    for creature in input_json:
      v2_pk = generate_v2_pk(creature, v2_doc_key)
      fields = creature['fields'] or {}
      # using creature pk at a key, store res & imnty data on 
      # `resistances_and_immunities_storage` dict
      resistances_and_immunities_storage[v2_pk] = {
        'damage_resistances_display': fields['damage_resistances'],
        'damage_immunities_display': fields['damage_immunities'],
        'damage_vulnerabilities_display': fields['damage_vulnerabilities'],
        'condition_immunities_display': fields['condition_immunities'],
      }

    updated_creatures_list = []

    # iterate over each creature in output json
    for creature in output_json:
      # get resistance/immunity data stashed from input json
      pk = creature['pk']
      data_from_storage = resistances_and_immunities_storage.get(pk, '')

      # update field on creature
      if data_from_storage:
        creature['fields']['damage_resistances_display'] = data_from_storage['damage_resistances_display']
        creature['fields']['damage_immunities_display'] = data_from_storage['damage_immunities_display']
        creature['fields']['damage_vulnerabilities_display'] = data_from_storage['damage_vulnerabilities_display']
        creature['fields']['condition_immunities_display'] = data_from_storage['condition_immunities_display']
      
      updated_creatures_list.append(creature)
    
    # Write modified output JSON
    write_json_file(output_path, updated_creatures_list)

      
      
# map of input/output files to process
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
    'v2_document_key': 'a5e-mm',
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