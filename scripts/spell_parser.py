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
            keyword_list = ['sphere', 'line', 'cone', 'cube', 'cylinder']
            context_word_list = ['feet', 'foot']
            attribute_name = 'shape'
            results = []
            for item in file_json:
                result={"name":slugify(item['name']),"keywordfound":False,"modified":False}
                
                #The ability to interact with objects is here!
                for keyword in keyword_list:
                    #print("Keyword: {}".format(keyword))
                    analysis = find_keyword_in_string(item['desc'], keyword)

                    result['keywordfound']=analysis[0]
                    if result['keywordfound']==True:
                        context_exists = find_keyword_context_in_string(item['desc'], keyword, 3,context_word_list)
                        print(slugify(item['name']) + "     " + keyword + "     " + analysis[1])
                        if context_exists:
                            choice='1'
                        else:
                            choice = input('1: Tag it\n2: Skip\n'.format(attribute_name, keyword, slugify(item['name'])))
                        if choice == '1':
                            print(slugify(item['name']) + " tagged with " + keyword)
                            result['modified']=True
                            result['shape']=keyword
                        if choice == '2':
                            print("skipping")
                results.append(result)
        print(results)
                
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