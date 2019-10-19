import os
from django.core.management.base import BaseCommand

class Command(BaseCommand):
  def handle(self, *args, **options):

    migrations = 'python manage.py makemigrations && pipenv run python manage.py migrate'
    collect_static = 'python manage.py collectstatic --noinput'
    populate_db= 'pipenv run python manage.py populatedb --flush ./data/WOTC_5e_SRD_v5.1/ && pipenv run python manage.py populatedb --append ./data/tome_of_beasts/ && pipenv run python manage.py populatedb --append ./data/creature_codex/ && pipenv run python manage.py populatedb --append ./data/open5e_original/'
    rebuild_index= 'pipenv run python manage.py update_index --remove'

    os.system(migrations)
    os.system(collect_static)
    os.system(populate_db)
    os.system(rebuild_index)