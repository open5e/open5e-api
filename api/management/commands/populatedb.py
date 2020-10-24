from django.core.management.base import BaseCommand, CommandError
import json
from . import importer as i
from api.models import Manifest
from pathlib import Path
import hashlib


def get_hash(filepath):
    # https://stackoverflow.com/a/1131238
    file_hash = hashlib.md5()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            file_hash.update(chunk)
    return file_hash.hexdigest()

class Command(BaseCommand):

    help = 'Loads all properly formatted data into the database from the given directory.'
    document = ''

    def add_arguments(self, parser):
        #Positional Arguments.
        parser.add_argument('directory', nargs='+', type=str, help='Directory that contains %model_name%.json files to be loaded.')

        # Named (optional) arguments

        parser.add_argument('--flush', action='store_true', help='Flushes all existing database data before adding new objects.',)

        parser.add_argument('--update', action='store_true', help='Updates existing database data based on slugs.')

        parser.add_argument('--append', action='store_true', help="[Default] Adds new objects if they dont already exist.")

        parser.add_argument('--testrun', action='store_true', help="Do not commit changes.")

    def handle(self, *args, **options):
        dir = options['directory']
        if options['flush']:
            self.stdout.write(self.style.WARNING('Flushing existing database.'))
        elif options['update'] and not options['append']:
            self.stdout.write(self.style.WARNING('Existing matching (by slug) objects are being updated.'))
        elif options['testrun']:
            self.stdout.write(self.style.WARNING('NO CHANGES WILL BE COMMITTED.'))
        elif options['append'] and not options['update']:
            self.stdout.write(self.style.WARNING('Inserting new items into the database. Skipping conflicts (if any).'))
        else:
            raise ValueError('Invalid options combination.')
        self.stdout.write(self.style.SUCCESS('Reading in files from {0}'.format(dir)))

        self.options = options

        if bool(options['flush']): Manifest.objects.all().delete()
        for dir in options['directory']:
            importer = i.Importer()
            with open(dir+'document.json', encoding="utf-8") as doc_data:
                docs = json.load(doc_data)
                self.stdout.write(self.style.SUCCESS(importer.DocumentImporter(options, docs)))
            
            bgs_file = Path(dir+'backgrounds.json')
            if bgs_file.exists():
                bgs_hash = get_hash(bgs_file)
                importer.ManifestImporter(options, bgs_file, bgs_hash)
                with open(bgs_file, encoding="utf-8") as bg_data:
                    bgs = json.load(bg_data)
                    self.stdout.write(self.style.SUCCESS(importer.BackgroundImporter(options, bgs)))

            cls_file = Path(dir+'classes.json')
            if cls_file.exists():
                cls_hash = get_hash(cls_file)
                importer.ManifestImporter(options, cls_file, cls_hash)
                with open(cls_file, encoding="utf-8") as cls_data:
                    cls = json.load(cls_data)
                    self.stdout.write(self.style.SUCCESS(importer.ClassImporter(options, cls)))

            con_file = Path(dir+'conditions.json')
            if con_file.exists():
                con_hash = get_hash(con_file)
                importer.ManifestImporter(options, con_file, con_hash)
                with open(con_file, encoding="utf-8") as con_data:
                    con = json.load(con_data)
                    self.stdout.write(self.style.SUCCESS(importer.ConditionImporter(options, con)))

            fea_file = Path(dir+'feats.json')
            if fea_file.exists():
                fea_hash = get_hash(fea_file)
                importer.ManifestImporter(options, fea_file, fea_hash)
                with open(fea_file, encoding="utf-8") as fea_data:
                    fea = json.load(fea_data)
                    self.stdout.write(self.style.SUCCESS(importer.FeatImporter(options, fea)))

            mag_file = Path(dir+'magicitems.json')
            if mag_file.exists():
                mag_hash = get_hash(mag_file)
                importer.ManifestImporter(options, mag_file, mag_hash)
                with open(mag_file, encoding="utf-8") as mag_data:
                    mag = json.load(mag_data)
                    self.stdout.write(self.style.SUCCESS(importer.MagicItemImporter(options, mag)))

            spl_file = Path(dir+'spells.json')
            if spl_file.exists():
                spl_hash = get_hash(spl_file)
                importer.ManifestImporter(options, spl_file, spl_hash)
                with open(spl_file, encoding="utf-8") as spl_data:
                    spl = json.load(spl_data)
                    self.stdout.write(self.style.SUCCESS(importer.SpellImporter(options, spl)))

            mon_file = Path(dir+'monsters.json')
            if mon_file.exists():
                mon_hash = get_hash(mon_file)
                importer.ManifestImporter(options, mon_file, mon_hash)
                with open(mon_file, encoding="utf-8") as mon_data:
                    mon = json.load(mon_data)
                    self.stdout.write(self.style.SUCCESS(importer.MonsterImporter(options, mon)))

            pln_file = Path(dir+'planes.json')
            if pln_file.exists():
                pln_hash = get_hash(pln_file)
                importer.ManifestImporter(options, pln_file, pln_hash)
                with open(pln_file, encoding="utf-8") as pln_data:
                    pln = json.load(pln_data)
                    self.stdout.write(self.style.SUCCESS(importer.PlaneImporter(options, pln)))

            sec_file = Path(dir+'sections.json')
            if sec_file.exists():
                sec_hash = get_hash(sec_file)
                importer.ManifestImporter(options, sec_file, sec_hash)
                with open(sec_file, encoding="utf-8") as sec_data:
                    sec = json.load(sec_data)
                    self.stdout.write(self.style.SUCCESS(importer.SectionImporter(options, sec)))

            rac_file = Path(dir+'races.json')
            if rac_file.exists():
                rac_hash = get_hash(rac_file)
                importer.ManifestImporter(options, rac_file, rac_hash)
                with open(rac_file, encoding="utf-8") as rac_data:
                    rac = json.load(rac_data)
                    self.stdout.write(self.style.SUCCESS(importer.RaceImporter(options, rac)))

            wea_file = Path(dir+'weapons.json')
            if wea_file.exists():
                wea_hash = get_hash(wea_file)
                importer.ManifestImporter(options, wea_file, wea_hash)
                with open(wea_file, encoding="utf-8") as wea_data:
                    wea = json.load(wea_data)
                    self.stdout.write(self.style.SUCCESS(importer.WeaponImporter(options, wea)))
