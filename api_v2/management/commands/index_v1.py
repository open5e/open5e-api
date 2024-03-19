

from django.core.management import call_command
from django.core.management.base import BaseCommand

from django.db import connection

from api import models as v1

class Command(BaseCommand):
    """Implementation for the `manage.py `index_v1` subcommand."""

    help = 'Build the v1 search index.'

    def handle(self, *args, **options) -> None:
        self.stdout.write('Creating Virtual Table.')
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE searchindex;")
            cursor.execute("CREATE VIRTUAL TABLE searchindex USING fts5(id, text, route, slug, document_slug);")


            indexed_table_names = ['api_magicitem']
            # Insert all magic items.
            for n in indexed_table_names:
                query = "INSERT INTO searchindex (id,text,route,slug,document_slug) SELECT 1, desc, route, slug, 'hi' from {}".format(n)
                cursor.execute(query)



