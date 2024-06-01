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
        if f_obj['filename'] != args.model:
            continue

        with open(f_obj['path'],'r',encoding='utf-8') as f_in:
            objs = json.load(f_in)

            # CHECK FOR KEYS THAT ARE NUMBERS, WARN IF EXISTS
            known_keys_non_numeric_exceptions = []
            if f_obj['filename'] in known_keys_non_numeric_exceptions:
                logger.debug("Skipping {}: file is known to have numeric keys.".format(f_obj['filename']))
            else:
                check_keys_non_numeric(objs, f_obj)
                #if args.fix: fix_keys_to_parent_level(objs, f_obj)

            # CHECK FOR KEYS THAT ARE NOT PROPERLY SLUGIFIED
            known_keys_are_slugified_exceptions = []
            if f_obj['filename'] in known_keys_are_slugified_exceptions:
                logger.debug("Skipping {}: file is known to have non-slugified keys.".format(f_obj['filename']))
            else:
                check_keys_are_slugified(objs, f_obj)

            # CHECK THAT KEYS MATCH THE FORMAT DOC_NAME, SLUGIFIED_NAME
            known_keys_doc_name_exceptions = []
            if f_obj['filename'] in known_keys_doc_name_exceptions:
                logger.debug("Skipping {}: file is known to have non-slugified keys.".format(f_obj['filename']))
            else:
                check_keys_doc_name(objs, f_obj)
                if args.fix: fix_keys_to_doc_name(objs, f_obj)


def check_keys_non_numeric(objs,f):
    for obj in objs:
        if isinstance(obj['pk'], numbers.Real):
            logger.warning("{} uses numeric pk".format(f['path']))

def fix_keys_num_to_parent_name(objs,f):
    objs_fixed=[]
    for obj in objs:
        if isinstance(obj['pk'], numbers.Real):
            if f['filename']=='FeatureItem.json':
                logger.warning("{} changing from numeric pk to string".format(f['path']))
                pk_value = "{}_{}".format(obj['fields']['parent'],slugify(obj['fields']['name']))
                logger.warning("CHANGING PK TO {}".format(pk_value))
                obj['pk'] = pk_value
                objs_fixed.append(obj)

    #if f['filename']=='BackgroundBenefit.json':
    #    with open(f['path'],'w',encoding='utf-8') as wf:
    #        json.dump(objs_fixed,wf,indent=2)
    #        wf.write('\n')

def check_keys_are_slugified(objs,f):
    for obj in objs:
        if obj['pk'] != slugify(obj['pk']):
            logger.warning("{}:{} does not have a slugifed pk".format(f['path'],obj['pk']))


def check_keys_doc_name(objs,f):
    child_models = ['BackgroundBenefit.json','ClassFeature.json']
    for obj in objs:

        if f['filename'] in child_models:
            if obj['pk'] != "{}_{}".format(slugify(obj['fields']['parent']),slugify(obj['fields']['name'])):
                logger.warning("{}:{} does not follow the parent-name_slugified-name format.".format(f['path'],obj['pk']))
            continue
        if f['filename']=='ClassFeatureItem.json':
            if obj['pk'] != "{}_{}".format(slugify(obj['fields']['parent']),slugify(obj['fields']['level'])):
                logger.warning("{}:{} does not follow the parent-name_level format.".format(f['path'],obj['pk']))
            continue
        if obj['pk'] != "{}_{}".format(slugify(f['doc']),slugify(obj['fields']['name'])):
            logger.warning("{}:{} does not follow the doc-key_slugified-name format.".format(f['path'],obj['pk']))
            continue

def fix_keys_to_doc_name(objs,f):
    objs_fixed=[]

    for obj in objs:
        if obj['pk'] != "{}_{}".format(slugify(f['doc']),slugify(obj['fields']['name'])):
            if f['filename']=='CreatureAction.json':
                logger.warning("{} changing to doc_name format".format(f['path']))
                pk_value = "{}_{}".format(obj['fields']['parent'],slugify(obj['fields']['name']))
                logger.warning("CHANGING PK TO {}".format(pk_value))
                
                obj['former_pk'] = obj['pk']
                obj['pk'] = pk_value
                objs_fixed.append(obj)


        related_path = "{}/{}/{}/{}/{}/".format(f['root'],f['dir'],f['schema'],f['publisher'],f['doc'])
        related_filenames = ['CreatureAttack.json']

    for obj in objs_fixed:
        for related_file in related_filenames:
            logger.warning("CHANGING RELATED PK IN {} TO {}".format(related_file,obj['pk']))
            refactor_relations(related_path+related_file,"parent",obj['former_pk'], obj['pk'])
        obj.pop('former_pk')

    if f['filename']=='CreatureAction.json':    
        with open(f['path'],'w',encoding='utf-8') as wf:
            json.dump(objs_fixed,wf,ensure_ascii=False,indent=2)
        pass

def fix_keys_to_parent_level(objs,f):
    objs_fixed=[]
    if f['filename']!='CreatureAction.json':
        return

    for obj in objs:
        if obj['pk'] != "{}_{}".format(slugify(obj['fields']['parent']),slugify(obj['fields']['level'])):
            if f['filename']=='ClassFeatureItem.json':
                logger.warning("{} changing to parent_level".format(f['path']))
                pk_value = "{}_{}".format(slugify(obj['fields']['parent']),slugify(obj['fields']['level']))
                logger.warning("CHANGING PK TO {}".format(pk_value))
                

                obj['pk'] = pk_value
                objs_fixed.append(obj)


    if f['filename']=='ClassFeatureItem.json':    
        with open(f['path'],'w',encoding='utf-8') as wf:
            json.dump(objs_fixed,wf,ensure_ascii=False,indent=2)




def refactor_relations(filename, key, former_pk, new_pk):
    refactored_objects = []
    if os.path.isfile(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            objs = json.load(f)
            if key == "parent":
                for obj in objs:
                    if obj['fields'][key] == former_pk:
                        obj['fields'][key] = new_pk
                    refactored_objects.append(obj)
            if key == "items":
                for obj in objs:
                    if former_pk in obj['fields'][key]:
                        obj['fields'][key].remove(former_pk)
                        obj['fields'][key].append(new_pk)
                    refactored_objects.append(obj)

        with open(filename,'w', encoding='utf-8') as o:
            json.dump(refactored_objects,o, ensure_ascii=False,indent=2)

def check_keys_doc_parent_name(objs,f):
    for obj in objs:
        if obj['pk'] != "{}_{}_{}".format(slugify(f['doc']),slugify(obj['parent']),slugify(obj['fields']['name'])):
            logger.warning("{}:{} does not follow the doc-key_slugified-parent_slugified-name format.".format(f['path'],obj['pk']))
            break


if __name__ == "__main__":
    main()