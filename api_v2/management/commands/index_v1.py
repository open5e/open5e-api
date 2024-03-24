

from django.core.management import call_command
from django.core.management.base import BaseCommand

from django.db import connection

from api import models as v1
from api_v2 import models as v2

class Command(BaseCommand):
    """Implementation for the `manage.py `index_v1` subcommand."""

    help = 'Build the v1 search index.'

    def unload_all(self):
        object_count = v2.SearchResult.objects.all().count()
        v2.SearchResult.objects.all().delete()
        print("UNLOADED_OBJECT_COUNT:{}".format(object_count))

    def load_model(self,model,schema):
        print("SCHEMA:{} OBJECT_COUNT:{} MODEL:{} TABLE_NAME:{}".format(
                    schema,
                    model.objects.all().count(),
                    model.__name__,
                    model._meta.db_table))
        
        search_results = []
        for o in model.objects.all():
            search_results.append(v2.SearchResult(
                document_pk=o.document.slug,
                document_name=o.document.title,
                object_pk=o.slug,
                object_name=o.name,
                object_route=o.route,
                schema_version="v1"
            ))
        
        v2.SearchResult.objects.bulk_create(search_results)

        #print("LOADED_OBJECT_COUNT:{}".format(v2.SearchResult.objects.all().count()))

    def load_index(self):
        with connection.cursor() as cursor:

            cursor.execute("DROP TABLE IF EXISTS search_index;")
            
            cursor.execute("CREATE VIRTUAL TABLE search_index USING FTS5(document_pk,document_name,object_pk,object_name,object_route,schema_version);")

            cursor.execute("INSERT INTO search_index (document_pk,document_name,object_pk,object_name,object_route,schema_version) SELECT document_pk,document_name,object_pk,object_name,object_route,schema_version FROM api_v2_searchresult")
    

    def check_fts_enabled(self):
        #import sqlite3
        with connection.cursor() as cursor:
            cursor.execute('pragma compile_options;')
            available_pragmas = cursor.fetchall()
            
            for pragma in available_pragmas:
                if pragma[0]=='ENABLE_FTS5':
                    print("FOUND PRAGMA {}, FTS5 IS ENABLED".format(pragma))

    def handle(self, *args, **options) -> None:
        
        self.check_fts_enabled()
        self.unload_all()
        self.load_model(v1.MagicItem,"v1")

        self.load_index()


