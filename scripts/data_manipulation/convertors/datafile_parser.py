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

            modified_bgs = []
            modified_bgbs = []
            unprocessed_items = []
            for item in file_json:

                # Process the main background.
                background_object = {}
                background_object['model'] = "api_v2.background"
                background_object['pk'] = slugify(item['name'])
                background_object['fields'] = dict({})
                background_object['fields']['name'] = item['name']
                background_object['fields']['desc'] = item['desc']
                background_object['fields']['document'] = ""
                
                # Process the background benefits.
                benefit_type_enum = ( 
                    ('ability-score_increases','ability_score_increase'),
                    ('skill-proficiencies','skill_proficiency'),
                    ('languages','language'),
                    ('tool-proficiencies','tool_proficiency'),
                    ('equipment','equipment'),
                    ('feature-name','feature'),
                    ('suggested-characteristics','suggested_characteristics'),
                    ('adventures-and-advancement','adventures-and-advancement')
                )
                for benefit_type in benefit_type_enum:
                    benefit_object = {}
                    benefit_object['model'] = 'api_v2.backgroundbenefit'
                    if benefit_type[0] in item:
                        benefit_object['fields'] = dict({})
                        benefit_object['fields']['type'] = benefit_type[1]
                        if benefit_type[1] == 'feature':
                            benefit_object['fields']['name'] = item[benefit_type[0]]
                            if 'feature-description' in item:
                                benefit_object['fields']['desc'] = item['feature-description']
                            else: benefit_object['fields']['desc'] = ""
                        else:
                            benefit_object['fields']['name'] = benefit_type[0].title().replace("_"," ").replace("-"," ")
                            benefit_object['fields']['desc'] = item[benefit_type[0]]
                        benefit_object['fields']['background'] = background_object['pk']
                    
                        modified_bgbs.append(benefit_object)
                modified_bgs.append(background_object)

             #   unprocessed_items.append(item)

            #print("Unprocessed count:{}".format(len(unprocessed_items)))
            print("Background count:  {}".format(len(modified_bgs)))
            print("Benefit count:  {}".format(len(modified_bgbs)))
         
            if not args.test:
                
                modified_file = str(file.parent)+"/"+file.stem + args.modifiedsuffix + file.suffix
                print('Writing modified objects to {}.'.format(modified_file))
                if(os.path.isfile(modified_file)):
                    print("File already exists!")
                    exit(0)
                with open(modified_file, 'w', encoding='utf-8') as s:
                    s.write(json.dumps(modified_bgs, ensure_ascii=False, indent=4))
                
                modifiedbgb_file = str(file.parent)+"/"+file.stem +"_benefits" + args.modifiedsuffix + file.suffix
                print('Writing modified objects to {}.'.format(modifiedbgb_file))
                if(os.path.isfile(modifiedbgb_file)):
                    print("File already exists!")
                    exit(0)
                with open(modifiedbgb_file, 'w', encoding='utf-8') as sbgb:
                    sbgb.write(json.dumps(modified_bgbs, ensure_ascii=False, indent=4))


                #unmodified_file = str(file.parent)+"/"+file.stem + args.unmodifiedsuffix + file.suffix
                #print('Writing unmodified objects to {}.'.format(unmodified_file))
                #with open(unmodified_file, 'w', encoding='utf-8') as s:
                #    s.write(json.dumps(unprocessed_items, ensure_ascii=False, indent=4))
            

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