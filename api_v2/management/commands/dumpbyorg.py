

import os
import json
import time

from django.core.management import call_command
from django.core.management.base import BaseCommand

from django.core import serializers

from django.apps import apps
from django.apps import AppConfig

from api_v2.models import *


class Command(BaseCommand):
    """Implementation for the `manage.py `dumpbyorg` subcommand."""

    help = 'Dump all data in structured directory.'

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

        rulesets = Ruleset.objects.all()
        write_queryset_data(options['dir'], rulesets, "Rulesets.json")

        licenses = License.objects.all()
        write_queryset_data(options['dir'], licenses, "Licenses.json")

        # Create a folder and Publisher fixture for each pubishing org.
        for pub in Publisher.objects.order_by('key'):
            pubq = Publisher.objects.filter(key=pub.key)
            pubdir = options['dir'] + "/{}".format(pub.key)
            write_queryset_data(pubdir, pubq, "Publisher.json")

            # Create a Document fixture for each document.
            for doc in Document.objects.filter(publisher=pub):
                docq = Document.objects.filter(key=doc.key)
                docdir = pubdir + "/{}".format(doc.key)
                write_queryset_data(docdir, docq, "Document.json")

                # Create a fixture for each nonblank model tied to a document.
                SKIPPED_MODEL_NAMES = [
                    'LogEntry',
                    'Ruleset',
                    'Publisher',
                    'Document',
                    'License',
                    'User',
                    'Session',
                    'ContentType',
                    'Permission']

                app_models = apps.get_models()

                for model in app_models:
                    if model.__name__ not in SKIPPED_MODEL_NAMES:

                        modelq = model.objects.all()
                        write_queryset_data(
                            docdir,
                            modelq,
                            model.__name__+".json")

                self.stdout.write(self.style.SUCCESS(
                    'Wrote {} to {}'.format(doc.key, docdir)))

        self.stdout.write(self.style.SUCCESS('Data dumping complete.'))


def write_queryset_data(filepath, queryset, filename):
    if queryset.count() > 0:
        if not os.path.exists(filepath):
            os.makedirs(filepath)

        output_filepath = filepath + "/" + filename
        with open(output_filepath, 'w', encoding='utf-8') as f:
            serializers.serialize("json", queryset, indent=2, stream=f)
