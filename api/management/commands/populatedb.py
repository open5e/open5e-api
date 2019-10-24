from django.core.management.base import BaseCommand, CommandError
import json
from . import importer as i
from pathlib import Path


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

        for dir in options['directory']:
            importer = i.Importer()
            with open(dir+'document.json', encoding="latin-1") as doc_data:
                docs = json.load(doc_data)
                self.stdout.write(self.style.SUCCESS(importer.DocumentImporter(options, docs)))
            
            bgs_file = Path(dir+'backgrounds.json')
            if bgs_file.exists():
                with open(bgs_file, encoding="latin-1") as bg_data:
                    bgs = json.load(bg_data)
                    self.stdout.write(self.style.SUCCESS(importer.BackgroundImporter(options, bgs)))

            cls_file = Path(dir+'classes.json')
            if cls_file.exists():
                with open(cls_file, encoding="latin-1") as cls_data:
                    cls = json.load(cls_data)
                    self.stdout.write(self.style.SUCCESS(importer.ClassImporter(options, cls)))

            con_file = Path(dir+'conditions.json')
            if con_file.exists():
                with open(con_file, encoding="latin-1") as con_data:
                    con = json.load(con_data)
                    self.stdout.write(self.style.SUCCESS(importer.ConditionImporter(options, con)))

            fea_file = Path(dir+'feats.json')
            if fea_file.exists():
                with open(fea_file, encoding="latin-1") as fea_data:
                    fea = json.load(fea_data)
                    self.stdout.write(self.style.SUCCESS(importer.FeatImporter(options, fea)))

            mag_file = Path(dir+'magicitems.json')
            if mag_file.exists():
                with open(mag_file, encoding="latin-1") as mag_data:
                    mag = json.load(mag_data)
                    self.stdout.write(self.style.SUCCESS(importer.MagicItemImporter(options, mag)))

            spl_file = Path(dir+'spells.json')
            if spl_file.exists():
                with open(spl_file, encoding="latin-1") as spl_data:
                    spl = json.load(spl_data)
                    self.stdout.write(self.style.SUCCESS(importer.SpellImporter(options, spl)))

            mon_file = Path(dir+'monsters.json')
            if mon_file.exists():
                with open(mon_file, encoding="latin-1") as mon_data:
                    mon = json.load(mon_data)
                    self.stdout.write(self.style.SUCCESS(importer.MonsterImporter(options, mon)))

            pln_file = Path(dir+'planes.json')
            if pln_file.exists():
                with open(pln_file, encoding="latin-1") as pln_data:
                    pln = json.load(pln_data)
                    self.stdout.write(self.style.SUCCESS(importer.PlaneImporter(options, pln)))

            sec_file = Path(dir+'sections.json')
            if sec_file.exists():
                with open(sec_file, encoding="latin-1") as sec_data:
                    sec = json.load(sec_data)
                    self.stdout.write(self.style.SUCCESS(importer.SectionImporter(options, sec)))

            rac_file = Path(dir+'races.json')
            if rac_file.exists():
                with open(rac_file, encoding="latin-1") as rac_data:
                    rac = json.load(rac_data)
                    self.stdout.write(self.style.SUCCESS(importer.RaceImporter(options, rac)))

            wea_file = Path(dir+'weapons.json')
            if wea_file.exists():
                with open(wea_file, encoding="latin-1") as wea_data:
                    wea = json.load(wea_data)
                    self.stdout.write(self.style.SUCCESS(importer.WeaponImporter(options, wea)))
