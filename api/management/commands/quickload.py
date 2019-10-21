
import os
from django.core.management.base import BaseCommand

class Command(BaseCommand):
  def handle(self, *args, **options):
    populate_db='pipenv run python manage.py populatedb --flush ./data/open5e_original/ && pipenv run python manage.py populatedb --append ./data/WOTC_5e_SRD_v5.1/ && pipenv run python manage.py populatedb --append ./data/tome_of_beasts/ && pipenv run python manage.py populatedb --append ./data/creature_codex/'

    os.system(populate_db)