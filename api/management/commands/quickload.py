import os

from django.core.management.base import BaseCommand

class Command(BaseCommand):
  def handle(self, *args, **options):
    populate_db='pipenv run python manage.py populatedb --flush ./data/open5e_original/ && pipenv run python manage.py populatedb --append ./data/WOTC_5e_SRD_v5.1/ && pipenv run python manage.py populatedb --append ./data/tome_of_beasts/ && pipenv run python manage.py populatedb --append ./data/creature_codex/ && pipenv run python manage.py populatedb --append ./data/tome_of_beasts_2/ && pipenv run python manage.py populatedb --append ./data/deep_magic/ && pipenv run python manage.py populatedb --append ./data/menagerie && pipenv run python manage.py populatedb --append ./data/tome_of_beasts_3'

    os.system(populate_db)
