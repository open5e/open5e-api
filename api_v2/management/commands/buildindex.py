
import argparse

from django.core.management import call_command
from django.core.management.base import BaseCommand

from django.db import connection

from api import models as v1
from api_v2 import models as v2

class Command(BaseCommand):
    """Implementation for the `manage.py `index_v1` subcommand."""

    help = 'Build the v1 search index.'

    def add_arguments(self, parser: argparse.ArgumentParser):
        """Define arguments for the `manage.py quicksetup` subcommand."""

        # Named (optional) arguments.
        parser.add_argument(
            "--v1",
            action="store_true",
            help="Explicitly adding v1 data to index.",
        )
        # Named (optional) arguments.
        parser.add_argument(
            "--v2",
            action="store_true",
            help="Explicitly adding v2 data to index.",
        )

    def unload_all_content(self):
        object_count = v2.SearchResult.objects.all().count()
        v2.SearchResult.objects.all().delete()
        print("UNLOADED_OBJECT_COUNT:{}".format(object_count))

    def load_v1_content(self, model):
        results = []
        standard_v1_models = ['MagicItem','Spell','Monster','CharClass','Archetype',
                'Race','Subrace','Plane','Section','Feat','Condition','Background','Weapon','Armor']

        if model.__name__ in standard_v1_models:
            for o in model.objects.all():
                results.append(v2.SearchResult(
                    document_pk=o.document.slug,
                    object_pk=o.slug,
                    object_name=o.name,
                    object_model=o.__class__.__name__,
                    schema_version="v1",
                    text=o.name+"\n"+o.desc

                ))
        return results

    def load_v2_content(self, model):
        results = []
        standard_v2_models = ['Item','Spell','Creature','CharacterClass','Race','Feat','Condition','Background','Environment']

        if model.__name__ in standard_v2_models:
            for o in model.objects.all():
                results.append(v2.SearchResult(
                    document_pk=o.document.key,
                    object_pk=o.pk,
                    object_name=o.name,
                    object_model=o.__class__.__name__,
                    schema_version='v2',
                    text=o.as_text()
                ))
        return results

    def load_content(self,model,schema):
        print("SCHEMA:{} OBJECT_COUNT:{} MODEL:{} TABLE_NAME:{}".format(
                    schema,
                    model.objects.all().count(),
                    model.__name__,
                    model._meta.db_table))

        if schema == 'v1':
            v2.SearchResult.objects.bulk_create(
                self.load_v1_content(model)
            )

        if schema == 'v2':
            v2.SearchResult.objects.bulk_create(
                self.load_v2_content(model)
            )

    def load_index(self):
        with connection.cursor() as cursor:

            cursor.execute("DROP TABLE IF EXISTS search_index;")

            cursor.execute(
                "CREATE VIRTUAL TABLE search_index " +
                "USING FTS5(document_pk,object_pk,object_name,object_model,text,schema_version);")

            cursor.execute(
                "INSERT INTO search_index " +
                "(document_pk,object_pk,object_name,object_model,text,schema_version) " +
                "SELECT document_pk,object_pk,object_name,object_model,text,schema_version " +
                "FROM api_v2_searchresult")

    def check_fts_enabled(self):
        #import sqlite3
        with connection.cursor() as cursor:
            cursor.execute('pragma compile_options;')
            available_pragmas = cursor.fetchall()
            
            for pragma in available_pragmas:
                if pragma[0]=='ENABLE_FTS5':
                    print("FOUND PRAGMA {}, FTS5 IS ENABLED".format(pragma))


    def handle(self, *args, **options):
        
        # Ensure FTS is enabled and ready to go.
        self.check_fts_enabled()

        # Clear out the content table.
        self.unload_all_content()

        if options["v1"]:
            # Load the v1 models into the content table.
            self.load_content(v1.MagicItem,"v1")
            self.load_content(v1.Spell,"v1")
            self.load_content(v1.Monster,"v1")
            self.load_content(v1.CharClass,"v1")
            self.load_content(v1.Race,"v1")
            self.load_content(v1.Subrace,"v1")
            self.load_content(v1.Plane,"v1")
            self.load_content(v1.Section,"v1")
            self.load_content(v1.Feat,"v1")
            self.load_content(v1.Condition,"v1")
            self.load_content(v1.Background,"v1")
            self.load_content(v1.Weapon,"v1")
            self.load_content(v1.Armor,"v1")

        if options["v2"]:
            # Load the v2 models into the content table.
            self.load_content(v2.Item,"v2")
            self.load_content(v2.Spell,"v2")
            self.load_content(v2.Creature,"v2")
            self.load_content(v2.CharacterClass,"v2")
            self.load_content(v2.Race,"v2")
            self.load_content(v2.Feat,"v2")
            self.load_content(v2.Condition,"v2")
            self.load_content(v2.Background,"v2")
            self.load_content(v2.Environment,"v2")

        # Take the content table's current data and load it into the index.
        self.load_index()

        # Unload content table (saves storage space.)
        self.unload_all_content()
