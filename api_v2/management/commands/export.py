

import os
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
                base_path=options['dir'])
            write_queryset_data(v1doc_path, v1docq)

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
                    base_path=options['dir'])
                write_queryset_data(model_path, modelq)

            self.stdout.write(self.style.SUCCESS(
                'Wrote {} to {}'.format(v1doc.slug, v1doc_path)))

        self.stdout.write(self.style.SUCCESS('Data for v1 data complete.'))

        # Start V2 output.
        rulesets = Ruleset.objects.all()
        ruleset_path = get_filepath_by_model(
            'Ruleset',
            'api_v2',
            base_path=options['dir'])
        write_queryset_data(ruleset_path, rulesets)

        license_path = get_filepath_by_model(
            'License',
            'api_v2',
            base_path=options['dir'])
        licenses = License.objects.all()
        write_queryset_data(license_path, licenses)

        # Create a folder and Publisher fixture for each pubishing org.
        for pub in Publisher.objects.order_by('key'):
            pubq = Publisher.objects.filter(key=pub.key).order_by('pk')
            pub_path = get_filepath_by_model(
                "Publisher",
                "api_v2",
                pub_key=pub.key,
                base_path=options['dir'])
            write_queryset_data(pub_path, pubq)

            # Create a Document fixture for each document.
            for doc in Document.objects.filter(publisher=pub):
                docq = Document.objects.filter(key=doc.key).order_by('pk')
                doc_path = get_filepath_by_model(
                    "Document",
                    "api_v2",
                    pub_key=pub.key,
                    doc_key=doc.key,
                    base_path=options['dir'])
                write_queryset_data(doc_path, docq)

                for model in app_models:
                    SKIPPED_MODEL_NAMES = ['Document', 'Ruleset', 'License', 'Publisher','SearchResult']
                    CHILD_MODEL_NAMES = ['RaceTrait', 'FeatBenefit', 'BackgroundBenefit', 'ClassFeatureItem', 'CastingOption']
                    
                    if model._meta.app_label == 'api_v2' and model.__name__ not in SKIPPED_MODEL_NAMES:
                        if model.__name__ in CHILD_MODEL_NAMES:
                            if model.__name__ == 'RaceTrait':
                                modelq = model.objects.filter(race__document=doc).order_by('pk')
                            if model.__name__ == 'FeatBenefit':
                                modelq = model.objects.filter(parent__document=doc).order_by('pk')
                            if model.__name__ == 'BackgroundBenefit':
                                modelq = model.objects.filter(parent__document=doc).order_by('pk')
                            if model.__name__ == 'CastingOption':
                                modelq = model.objects.filter(spell__document=doc).order_by('pk')
                            if model.__name__ == 'ClassFeatureItem':
                                modelq = model.objects.filter(parent__document=doc).order_by('pk')
                        else:
                            modelq = model.objects.filter(document=doc).order_by('pk')
                        model_path = get_filepath_by_model(
                            model.__name__,
                            model._meta.app_label,
                            pub_key=pub.key,
                            doc_key=doc.key,
                            base_path=options['dir'])
                        write_queryset_data(model_path, modelq)

                self.stdout.write(self.style.SUCCESS(
                    'Wrote {} to {}'.format(doc.key, doc_path)))

        self.stdout.write(self.style.SUCCESS('Data for v2 data complete.'))


def get_filepath_by_model(model_name, app_label, pub_key=None, doc_key=None, base_path=None):

    if app_label == "api_v2":
        root_folder_name = 'v2'
        root_models = ['License', 'Ruleset']
        pub_models = ['Publisher']

        if model_name in root_models:
            return "/".join((base_path, root_folder_name, model_name+".json"))

        if model_name in pub_models:
            return "/".join((base_path, root_folder_name, pub_key, model_name+".json"))

        else:
            return "/".join((base_path, root_folder_name, pub_key, doc_key, model_name+".json"))

    if app_label == "api":
        root_folder_name = 'v1'
        root_models = ['Manifest']
        doc_folder_name = doc_key

        if model_name in root_models:
            return "/".join((base_path, root_folder_name, model_name+".json"))

        else:
            return "/".join((base_path, root_folder_name, doc_key, model_name+".json"))


def write_queryset_data(filepath, queryset):
    if queryset.count() > 0:
        dir = os.path.dirname(filepath)
        if not os.path.exists(dir):
            os.makedirs(dir)

        output_filepath = filepath
        with open(output_filepath, 'w', encoding='utf-8') as f:
            serializers.serialize("json", queryset, indent=2, stream=f)


def get_model_queryset_by_document(model, doc):
    print("Getting the queryset for: {}".format(model.__name__))

    if model.__name__ in ['Trait']:
        return model.objects.filter(race__document=doc).order_by('pk')

    if model.__name__ in ['BackgroundBenefit']:
        return model.objects.filter(background__document=doc).order_by('pk')

    if model.__name__ in ['FeatBenefit']:
        return model.objects.filter(feat__document=doc).order_by('pk')

    return model.objects.filter(document=doc).order_by('pk')