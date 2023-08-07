import sys
import os
import argparse
import json
import re

from pathlib import Path

from django.template.defaultfilters import slugify

def main():
    try:

        parser = argparse.ArgumentParser(epilog='v{}')
        parser.add_argument('-d', '--datadir',
            help='Data directory')
        parser.add_argument('-f', '--filename',
            help='Filename to parse. This will determine expected structure.')
        parser.add_argument('-r', '--recursive', action='store_true',
            help='Find filename recursively below datadir.')

        parser.add_argument('--modifiedsuffix', default='_modified',
            help='Suffix for the output filename of changed items.')

        parser.add_argument('--unmodifiedsuffix', default='_unchanged',
            help='Suffix for the output filename of unchanged items.')


        parser.add_argument('-t', '--test', action='store_true', default=False,
            help='Do not write output files.')

        args = parser.parse_args()

        if len(sys.argv) < 2:
            parser.print_help()
            sys.exit(0)

        ## Look in Data Dir, and print out all the files that match filename.
        if os.path.isdir(args.datadir):
            print("Data directory {} exists.".format(args.datadir))
        
        print("In scope files:")
        in_scope_files = []
        if not args.recursive:
            data_file = Path(args.datadir + "/" +args.filename)
            in_scope_files.append(data_file)
            print("{} [{}]".format(data_file.name, data_file.parent.name))

        ## Do it in all subfolders too if recursive is true.
        else:
            for path in Path(args.datadir).rglob('**/'+args.filename):
                in_scope_files.append(path)
                print("{} [{}]".format(path.name, path.parent.name))


        for file in in_scope_files:
            print("Opening and parsing {}".format(file.name))
            file_json = json.load(file.open())
            print("File Loaded")

            modified_items = []
            unprocessed_items = []
            for item in file_json:
                any_armor = ['studded-leather','splint','scale-mail','ring-mail','plate','padded','leather','hide','half-plate','chain-shirt','chain-mail','breastplate']
                light = ['studded-leather','padded','leather']
                any_med_heavy = ['splint','scale-mail','ring-mail','plate','hide','half-plate','chain-shirt','chain-mail','breastplate']
                any_heavy = ['splint','ring-mail','plate','chain-mail']

                any_sword_slashing = ['shortsword','longsword','greatsword', 'scimitar']
                any_axe = ['handaxe','battleaxe','greataxe']
                any_weapon = [
                    'club',
                    'dagger',
                    'greatclub',
                    'handaxe',
                    'javelin',
                    'light-hammer',
                    'mace',
                    'quarterstaff',
                    'sickle',
                    'spear',
                    'battleaxe',
                    'flail',
                    'lance',
                    'longsword',
                    'morningstar',
                    'rapier',
                    'scimitar',
                    'shortsword',
                    'trident',
                    'warpick',
                    'warhammer',
                    'whip',
                    'blowgun',
                    'net']

                item_model={"model":"api_v2.item"}
                item_model['pk'] = slugify(item['name'])
                item_model['fields'] = dict({})
                item_model['fields']['name'] = item['name']
                item_model['fields']['desc']=item["desc"]
                item_model['fields']['size']=1
                item_model['fields']['weight']=str(0.0)
                item_model['fields']['armor_class']=0
                item_model['fields']['hit_points']=0
                item_model['fields']['document']="vault-of-magic"
                item_model['fields']['cost']=0
                item_model['fields']['weapon']=None
                item_model['fields']['armor']=None
                item_model['fields']['requires_attunement']=False
                if "requires-attunement" in item:
                    if item["requires-attunement"]=="requires attunement":
                        item_model['fields']['requires_attunement']=True
                #if item["rarity"] not in ['common','uncommon','rare','very rare','legendary']:
                #    print(item['name'], item['rarity'])
                #    unprocessed_items.append(item)
                #    continue

                if item['rarity'] == 'common':
                    item_model['fields']['rarity'] = 1
                if item['rarity'] == 'uncommon':
                    item_model['fields']['rarity'] = 2
                if item['rarity'] == 'rare':
                    item_model['fields']['rarity'] = 3
                if item['rarity'] == 'very rare':
                    item_model['fields']['rarity'] = 4
                if item['rarity'] == 'legendary':
                    item_model['fields']['rarity'] = 5

                if item['type'] != "Potion":
                    unprocessed_items.append(item)
                    continue
                
                if 'Unstable Bombard' not in item['name']:
                    unprocessed_items.append(item)
                    continue

                item_model['fields']['category']="potion"
                item_model['fields']['rarity'] = 3

                for f in ["mindshatter","murderous","sloughide"]:
                   # for x,rar in enumerate(['uncommon','rare','very rare']):
                    item_model['fields']['name']= "{} Bombard".format(f.title())
                    #item_model['fields']['name'] = item['name']
                    #item_model['fields']['armor'] = 'leather'
                    item_model['pk'] = slugify(item_model['fields']["name"])
                    print_item = json.loads(json.dumps(item_model))
                    modified_items.append(print_item)

#                modified_items.append(item_model)

            print("Unprocessed count:{}".format(len(unprocessed_items)))
            print("Processed count:  {}".format(len(modified_items)))
            
           
            if not args.test:
                
                modified_file = str(file.parent)+"/"+file.stem + args.modifiedsuffix + file.suffix
                print('Writing modified objects to {}.'.format(modified_file))
                if(os.path.isfile(modified_file)):
                    print("File already exists!")
                    exit(0)
                with open(modified_file, 'w', encoding='utf-8') as s:
                    s.write(json.dumps(modified_items, ensure_ascii=False, indent=4))
                
                unmodified_file = str(file.parent)+"/"+file.stem + args.unmodifiedsuffix + file.suffix
                print('Writing unmodified objects to {}.'.format(unmodified_file))
                with open(unmodified_file, 'w', encoding='utf-8') as s:
                    s.write(json.dumps(unprocessed_items, ensure_ascii=False, indent=4))
            

    except Exception as e:
        print(e)

def find_keyword_in_string(string, keyword):
    if keyword in string:
        context = string[string.index(keyword)-40:string.index(keyword)+40]

        return (True, context)
    else:
        return (False, None)

def find_keyword_context_in_string(string, keyword, distance, cwl):
    context = string[string.index(keyword)-40:string.index(keyword)+40]
    for context_word in cwl:
        if context_word in context:
            return True

    return False


if __name__ == '__main__':
    main()