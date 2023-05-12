import requests
import argparse
import json
import sys

def main():

    parser = argparse.ArgumentParser(epilog='v{}')
    parser.add_argument('-o', '--output',
        help='Output directory.')
    args = parser.parse_args()

    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(0)
    # class names
    class_names = [
        "bard","wizard","sorcerer","cleric","druid","ranger","warlock"
    ]
    # document slugs
    document_slugs = [
        "wotc-srd","o5e","tob","tob","cc","tob2","dmag","menagerie","tob3","a5e","kp","dmag-e","warlock","vom"
        ]

# for each document
# make a call to the api like this: https://api.open5e.com/spells/?dnd_class__icontains=ritual&document__slug=wotc-srd
# parse through all the results and output them into a spelllist.json.

    for slug in document_slugs:
        spelllist_doc = []
        url = 'https://api.open5e.com/spells/'
        parameters = {
            'document__slug': slug,
            'format':'json',
            'fields':'slug',
            'limit':1000
        }
        with open("{}/{}_spelllist.json".format(args.output, slug),'w') as o:
            write_out = False
            for class_name in class_names:
                parameters['dnd_class__icontains']=class_name
                print("About to make a request out to {} with params {}".format(url, parameters))
                response_json = requests.get(url, params=parameters).json()
        
                if int(response_json['count'])>0:
                    write_out = True
                    spelllist = {"name":class_name}
                    spelllist['spell_list']=[]
                    for spell in response_json['results']:
                        spelllist['spell_list'].append(spell['slug'])
                    spelllist_doc.append(spelllist)

            if write_out:
                json.dump(spelllist_doc, o, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    main()