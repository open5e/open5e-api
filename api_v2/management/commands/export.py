

import os
import csv
import json
import time

from django.core.management import call_command
from django.core.management.base import BaseCommand

from django.core import serializers

from django.apps import apps
from django.apps import AppConfig

from api_v2.models import *
from api import models as v1

class Command(BaseCommand):
    """Implementation for the `manage.py `export` subcommand."""

    help = 'Export all v2 model data in structured directory.'

    def add_arguments(self, parser):
        parser.add_argument("-d",
                            "--dir",
                            type=str,
                            help="Directory to write files to.")

        parser.add_argument("-f",
                            "--format",
                            type=str,
                            choices = ['csv','json'],
                            default = 'json',
                            help="File format of the output files.")


    def handle(self, *args, **options) -> None:
        
        self.stdout.write('Checking if directory exists.')
        if os.path.exists(options['dir']) and os.path.isdir(options['dir']):
            self.stdout.write('Directory {} exists.'.format(options['dir']))
        else:
            self.stdout.write(self.style.ERROR(
                'Directory {} does not exist.'.format(options['dir'])))
            exit(0)

        app_models = apps.get_models()

        # Start v1 output.
        v1documents = v1.Document.objects.all()
        for v1doc in v1documents:
            v1docq = v1.Document.objects.filter(slug=v1doc.slug).order_by('pk')
            v1doc_path = get_filepath_by_model(
                "Document",
                "api",
                doc_key=v1doc.slug,
                base_path=options['dir'],
                format=options['format'])
            write_queryset_data(v1doc_path, v1docq, format=options['format'])

            for model in app_models:
                if model._meta.app_label == 'api':
                    if model.__name__ == "MonsterSpell":
                        modelq = model.objects.filter(monster__document=v1doc).order_by('pk')
                    SKIPPED_MODEL_NAMES = ['Document', 'Manifest','MonsterSpell']
                    if model.__name__ not in SKIPPED_MODEL_NAMES:
                        modelq = model.objects.filter(document=v1doc).order_by('pk')
                    else: continue
                else:
                    continue
                model_path = get_filepath_by_model(
                    model.__name__,
                    model._meta.app_label,
                    doc_key=v1doc.slug,
                    base_path=options['dir'],
                    format=options['format'])
                write_queryset_data(model_path, modelq, format=options['format'])

            self.stdout.write(self.style.SUCCESS(
                'Wrote {} to {}'.format(v1doc.slug, v1doc_path)))

        self.stdout.write(self.style.SUCCESS('Data for v1 data complete.'))

        # Start V2 output.
        rulesets = Ruleset.objects.all()
        ruleset_path = get_filepath_by_model(
            'Ruleset',
            'api_v2',
            base_path=options['dir'],
            format=options['format'])
        write_queryset_data(ruleset_path, rulesets, format=options['format'])

        license_path = get_filepath_by_model(
            'License',
            'api_v2',
            base_path=options['dir'],
            format=options['format'])
        licenses = License.objects.all()
        write_queryset_data(license_path, licenses, format=options['format'])

        # Create a folder and Publisher fixture for each pubishing org.
        for pub in Publisher.objects.order_by('key'):
            pubq = Publisher.objects.filter(key=pub.key).order_by('pk')
            pub_path = get_filepath_by_model(
                "Publisher",
                "api_v2",
                pub_key=pub.key,
                base_path=options['dir'],
                format=options['format'])
            write_queryset_data(pub_path, pubq, format=options['format'])

            # Create a Document fixture for each document.
            for doc in Document.objects.filter(publisher=pub):
                docq = Document.objects.filter(key=doc.key).order_by('pk')
                doc_path = get_filepath_by_model(
                    "Document",
                    "api_v2",
                    pub_key=pub.key,
                    doc_key=doc.key,
                    base_path=options['dir'],
                    format=options['format'])
                write_queryset_data(doc_path, docq, format=options['format'])

                for model in app_models:
                    SKIPPED_MODEL_NAMES = ['Document', 'Ruleset', 'License', 'Publisher','SearchResult']
                    CHILD_MODEL_NAMES = ['RaceTrait', 'FeatBenefit', 'BackgroundBenefit', 'ClassFeatureItem', 'SpellCastingOption','CreatureAction', 'CreatureTrait']
                    CHILD_CHILD_MODEL_NAMES = ['CreatureActionAttack']
                    
                    if model._meta.app_label == 'api_v2' and model.__name__ not in SKIPPED_MODEL_NAMES:
                        modelq=None
                        if model.__name__ in CHILD_CHILD_MODEL_NAMES:
                            modelq = model.objects.filter(parent__parent__document=doc).order_by('pk')
                        if model.__name__ in CHILD_MODEL_NAMES:
                            modelq = model.objects.filter(parent__document=doc).order_by('pk')
                        if modelq is None:
                            modelq = model.objects.filter(document=doc).order_by('pk')
                        model_path = get_filepath_by_model(
                            model.__name__,
                            model._meta.app_label,
                            pub_key=pub.key,
                            doc_key=doc.key,
                            base_path=options['dir'],
                            format=options['format'])
                        write_queryset_data(model_path, modelq, format=options['format'])

                self.stdout.write(self.style.SUCCESS(
                    'Wrote {} to {}'.format(doc.key, doc_path)))

        self.stdout.write(self.style.SUCCESS('Data for v2 data complete.'))


def get_filepath_by_model(model_name, app_label, pub_key=None, doc_key=None, base_path=None, format='json'):
    if not format.startswith('.'):
        file_ext = "."+format
    else:
        file_ext = format

    if app_label == "api_v2":
        root_folder_name = 'v2'
        root_models = ['License', 'Ruleset']
        pub_models = ['Publisher']
        
        if model_name in root_models:
            return "/".join((base_path, root_folder_name, model_name+file_ext))

        if model_name in pub_models:
            return "/".join((base_path, root_folder_name, pub_key, model_name+file_ext))

        else:
            return "/".join((base_path, root_folder_name, pub_key, doc_key, model_name+file_ext))

    if app_label == "api":
        root_folder_name = 'v1'
        root_models = ['Manifest']
        doc_folder_name = doc_key

        if model_name in root_models:
            return "/".join((base_path, root_folder_name, model_name+file_ext))

        else:
            return "/".join((base_path, root_folder_name, doc_key, model_name+file_ext))


def write_queryset_data(filepath, queryset, format='json'):
    if queryset.count() > 0:
        dir = os.path.dirname(filepath)
        if not os.path.exists(dir):
            os.makedirs(dir)

        output_filepath = filepath

        with open(output_filepath, 'w', encoding='utf-8') as f:
            if format=='json':
                serializers.serialize("json", queryset, indent=2, stream=f)
            if format=='csv':
                # Create headers:
                fieldnames = []
                for field in queryset.first().__dict__.keys():
                    if not field.startswith("_"):
                        fieldnames.append(field)
                
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(queryset.values())

