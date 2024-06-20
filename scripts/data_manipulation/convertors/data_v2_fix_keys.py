import argparse
import json
import numbers
import glob
import os

import logging
logger = logging.getLogger(__name__)
from django.template.defaultfilters import slugify


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--directory', default='./data/v2',
        help='Input data directory containing fixtures for v2 models.')
    parser.add_argument('-l','--loglevel', default='INFO',
        help='Log level.')
    parser.add_argument('-f', '--fix', action='store_true',
        help='If this flag is set, the script will automatically fix what it can.')

    parser.add_argument('-m','--model',
        help='Model name to operate on. All others will be skipped.')
    args = parser.parse_args()
        
    if args.loglevel == 'INFO':
        ll=logging.INFO
    if args.loglevel == 'DEBUG':
        ll=logging.DEBUG
    if args.loglevel == 'WARN':
        ll=logging.WARN
    logging.basicConfig(level=ll)

    # Get a list of files
    files = glob.glob(args.directory + '/**/*.json', recursive=True)
    excluded_files = ['Publisher.json','Document.json','Ruleset.json','License.json']
    file_list = []

    for file in files:
        if file.split("/")[-1] not in excluded_files:
            f = dict()
            f['path'] = file
            f['root'] = file.split("/")[0]
            f['dir'] = file.split("/")[1]
            f['schema'] = file.split("/")[2]
            try:
                f['publisher'] = file.split("/")[3]
            except IndexError:
                f['publisher'] = None

            try:
                f['doc'] = file.split("/")[4]
            except IndexError:
                f['doc'] = None

            f['filename'] = file.split("/")[-1]
            file_list.append(f)
        else:
            logger.debug("Excluding {} from file list".format(file))

    # LOOPING THROUGH ALL IN-SCOPE FILES
    for f_obj in file_list:
        if f_obj['filename'] != 'Creature.json':
            continue

        with open(f_obj['path'],'r',encoding='utf-8') as f_in:
            objs = json.load(f_in)
            for obj in objs:
                refactor_all(obj,f_obj)

            # Calculate keys for Creature.json

            # Calculate keys for CreatureAction.json
            

            # Calculate keys for CreatureActionAttack.json


        
def refactor_all(obj,f_obj):
    ca_path = "{}/{}/{}/{}/{}/{}".format(f_obj['root'],f_obj['dir'],f_obj['schema'],f_obj['publisher'],f_obj['doc'],'CreatureAction.json')
    caa_path = "{}/{}/{}/{}/{}/{}".format(f_obj['root'],f_obj['dir'],f_obj['schema'],f_obj['publisher'],f_obj['doc'],'CreatureActionAttack.json')
    
    old_creature_key = obj['pk']
    new_creature_key = "{}_{}".format(slugify(f_obj['doc']),slugify(obj['fields']['name']))
    refactor_key(f_obj['path'], obj['pk'], new_creature_key)

    # Rewrite parent references.
    refactor_parent_reference(ca_path,old_creature_key,new_creature_key)

    # Open CreatureAction.json
    with open(ca_path, 'r', encoding='utf-8') as ca_f:
        ca_objs = json.load(ca_f)
        for ca_obj in ca_objs:
            ca_old_key = ca_obj['pk']
            ca_new_key = "{}_{}".format(ca_obj['fields']['parent'],slugify(ca_obj['fields']['name']))
            refactor_key(ca_path,ca_old_key,ca_new_key)
            refactor_parent_reference(caa_path,ca_old_key,ca_new_key)

    with open(caa_path, 'r', encoding='utf-8') as caa_f:
        caa_objs = json.load(caa_f)
        for caa_obj in caa_objs:
            caa_old_key = caa_obj['pk']
            caa_new_key = "{}_{}".format(caa_obj['fields']['parent'],slugify(caa_obj['fields']['name']))
            refactor_key(caa_path,caa_old_key,caa_new_key)


def refactor_parent_reference(file, old_parent, new_parent):
    refactored_objects = []
    with open(file, 'r', encoding='utf-8') as f:
        objs = json.load(f)
        for obj in objs:
            if obj['fields']['parent']==old_parent:
                obj['fields']['parent'] = new_parent
            refactored_objects.append(obj)
   
    logger.warning("refactoring parent {} {} {}".format(file, old_parent, new_parent))
    with open(file,'w', encoding='utf-8') as o:
        json.dump(refactored_objects,o, ensure_ascii=False,indent=2)

def refactor_key(file, old_key, new_key):
    refactored_objects = []
    with open(file, 'r', encoding='utf-8') as f:
        objs = json.load(f)
        for obj in objs:
            if obj['pk']==old_key:
                obj['pk'] = new_key
            refactored_objects.append(obj)
   
    logger.warning("refactoring key {} {} {}".format(file, old_key, new_key))
    with open(file,'w', encoding='utf-8') as o:
        json.dump(refactored_objects,o, ensure_ascii=False,indent=2)



if __name__ == "__main__":
    main()