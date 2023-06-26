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

            #item_model={"mode":"api_v2.item","fields":{}}

            modified_items = []
            unprocessed_items = []
            for item in file_json:

                armor_keys = ['studded-leather','splint','scale-mail','ring-mail','plate','padded','leather','hide','half-plate','chain-shirt','chain-mail','breastplate']
                weapon_keys = []

                if item['type'] not in ["Wondrous item","Rod","Staff","Potion","Scroll","Wand","Ring","Armor (shield)",
                    "Armor (scale mail)"]:
                    unprocessed_items.append(item)
                    continue

                if item['type'] == "Wondrous item":
                    item['type']='wondrous'

                if item['type'] == "Armor (plate)":
                    item['type']='armor'

                item_model={"model":"api_v2.item","fields":{}}
                item_model['fields']['armor']='scale-mail'
                item_model['pk']=slugify(item["name"])
                item_model['fields']['name']=item["name"]
                item_model['fields']['desc']=item["desc"]
                item_model['fields']['category']=item['type'].lower()
                item_model['fields']['size']=1
                item_model['fields']['weight']=0.0
                item_model['fields']['armor_class']=0
                item_model['fields']['hit_points']=0
                item_model['fields']['document']="srd"
                item_model['fields']['cost']=None
                item_model['fields']['weapon']=None
                #item_model['fields']['armor']=None
                item_model['fields']['requires_attunement']=False
                if "requires-attunement" in item:
                    if item["requires-attunement"]=="requires attunement":
                        item_model['fields']['requires_attunement']=True
                if item["rarity"] not in ['common','uncommon','rare','very rare','legendary']:
                    #print(item['name'], item['rarity'])
                    unprocessed_items.append(item)
                    continue
                else:
                    if item["rarity"] == 'common':
                        item_model['fields']['rarity'] = 1
                    if item["rarity"] == 'uncommon':
                        item_model['fields']['rarity'] = 2
                    if item["rarity"] == 'rare':
                        item_model['fields']['rarity'] = 3
                    if item["rarity"] == 'very rare':
                        item_model['fields']['rarity'] = 4
                    if item["rarity"] == 'legendary':
                        item_model['fields']['rarity'] = 5
 
                modified_items.append(item_model)

            print("Unprocessed count:{}".format(len(unprocessed_items)))

            sister_file = str(file.parent)+"/"+file.stem + "_modified" + file.suffix
            with open(sister_file, 'w', encoding='utf-8') as s:
                s.write(json.dumps(modified_items, ensure_ascii=False, indent=4))
            
            unprocced = str(file.parent)+"/"+file.stem + "_unprocessed" + file.suffix
            with open(unprocced, 'w', encoding='utf-8') as s:
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