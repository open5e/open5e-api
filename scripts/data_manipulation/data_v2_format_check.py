import argparse
import json
import numbers
import glob

import logging
logger = logging.getLogger(__name__)

from django.template.defaultfilters import slugify


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--directory', default='./data/v2',
        help='Input data directory containing fixtures for v2 models.')
    parser.add_argument('-l','--loglevel', default='INFO',
        help='Log level.')
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
        with open(f_obj['path'],'r',encoding='utf-8') as f_in:
            objs = json.load(f_in)

            # CHECK FOR KEYS THAT ARE NUMBERS, WARN IF EXISTS
            known_keys_non_numeric_exceptions = ['CastingOption.json','Capability.json','Trait.json','FeatureItem.json']
            if f_obj['filename'] in known_keys_non_numeric_exceptions:
                logger.debug("Skipping {}: file is known to have numeric keys.".format(f_obj['filename']))
            else:
                check_keys_non_numeric(objs, f_obj)
                #fix_keys_num_to_parent_name(objs, f_obj)
            '''
            # CHECK FOR KEYS THAT ARE NOT PROPERLY SLUGIFIED
            known_keys_are_slugified_exceptions = ['CastingOption.json','Capability.json','BackgroundBenefit.json','Trait.json','FeatureItem.json']
            if f_obj['filename'] in known_keys_are_slugified_exceptions:
                logger.debug("Skipping {}: file is known to have non-slugified keys.".format(f_obj['filename']))
            else:
                check_keys_are_slugified(objs, f_obj)
            '''
            # CHECK THAT KEYS MATCH THE FORMAT DOC_NAME, SLUGIFIED_NAME
            known_keys_doc_name_exceptions = ['CastingOption.json','Capability.json','BackgroundBenefit.json','Trait.json','FeatureItem.json', 'Size.json','CreatureAttack.json']
            if f_obj['filename'] in known_keys_doc_name_exceptions:
                logger.debug("Skipping {}: file is known to have non-slugified keys.".format(f_obj['filename']))
            else:
                check_keys_doc_name(objs, f_obj)
                fix_keys_to_doc_name(objs, f_obj)


def check_keys_non_numeric(objs,f):
    for obj in objs:
        if isinstance(obj['pk'], numbers.Real):
            logger.warning("{} uses numeric pk".format(f['path']))

def fix_keys_num_to_parent_name(objs,f):
    for obj in objs:
        if isinstance(obj['pk'], numbers.Real):
            if f['filename']=='BackgroundBenefit.json':
                logger.warning("{} changing from numeric pk to string".format(f['path']))
                pk_value = "{}_{}".format(obj['fields']['parent'],slugify(obj['fields']['name']))
                logger.warning("CHANGING PK TO {}".format(pk_value))

def check_keys_are_slugified(objs,f):
    for obj in objs:
        if obj['pk'] != slugify(obj['pk']):
            logger.warning("{}:{} does not have a slugifed pk".format(f['path'],obj['pk']))


def check_keys_doc_name(objs,f):
    for obj in objs:
        if obj['pk'] != "{}_{}".format(slugify(f['doc']),slugify(obj['fields']['name'])):
            logger.warning("{}:{} does not follow the doc-key_slugified-name format.".format(f['path'],obj['pk']))
            break

def fix_keys_to_doc_name(objs,f):
    for obj in objs:
        if obj['pk'] != "{}_{}".format(slugify(f['doc']),slugify(obj['fields']['name'])):
            if f['filename']=='Background.json':
                logger.warning("{} changing to doc_name format".format(f['path']))
                pk_value = "{}_{}".format(obj['fields']['document'],slugify(obj['fields']['name']))
                logger.warning("CHANGING PK TO {}".format(pk_value))



def check_keys_doc_parent_name(objs,f):
    for obj in objs:
        if obj['pk'] != "{}_{}_{}".format(slugify(f['doc']),slugify(obj['parent']),slugify(obj['fields']['name'])):
            logger.warning("{}:{} does not follow the doc-key_slugified-parent_slugified-name format.".format(f['path'],obj['pk']))
            break


if __name__ == "__main__":
    main()