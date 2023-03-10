import hashlib
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from api.management.commands.importer import Importer, ImportOptions, ImportSpec
from api import models


def _get_md5_hash(filepath: Path) -> str:
    """Construct an md5 hash for a file, using chunks to accomodate large files.

    Cribbed from https://stackoverflow.com/a/1131238.
    """
    file_hash = hashlib.md5()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            file_hash.update(chunk)
    return file_hash.hexdigest()


class Command(BaseCommand):

    help = "Loads all properly formatted data into the database from the given directories."
    document = ""

    def add_arguments(self, parser):
        # Positional Arguments.
        parser.add_argument(
            "directories",
            nargs="+",
            type=str,
            help="Directories that contains %model_name%.json files to be loaded.",
        )

        # Named (optional) arguments

        parser.add_argument(
            "--flush",
            action="store_true",
            help="Flushes all existing database data before adding new objects.",
        )

        parser.add_argument(
            "--update",
            action="store_true",
            help="Updates existing database data based on slugs.",
        )

        parser.add_argument(
            "--append",
            action="store_true",
            help="[Default] Adds new objects if they dont already exist.",
        )

        parser.add_argument(
            "--testrun", action="store_true", help="Do not commit changes."
        )

    def handle(self, *args, **options):
        directories = options["directories"]
        if options["flush"]:
            self.stdout.write(self.style.WARNING("Flushing existing database."))
        elif options["update"] and not options["append"]:
            self.stdout.write(
                self.style.WARNING(
                    "Existing matching (by slug) objects are being updated."
                )
            )
        elif options["testrun"]:
            self.stdout.write(self.style.WARNING("NO CHANGES WILL BE COMMITTED."))
        elif options["append"] and not options["update"]:
            self.stdout.write(
                self.style.WARNING(
                    "Inserting new items into the database. Skipping conflicts (if any)."
                )
            )
        else:
            raise ValueError("Invalid options combination.")

        self.options = options

        if bool(options["flush"]):
            models.Manifest.objects.all().delete()

        for directory in options["directories"]:
            self._populate_from_directory(Path(directory))

    def _populate_from_directory(self, directory: Path) -> None:
        self.stdout.write(self.style.SUCCESS(f"Reading in files from {directory}"))

        importer = Importer()
        import_options = ImportOptions(
            flush=self.options["flush"],
            update=self.options["update"],
            testrun=self.options["testrun"],
            append=self.options["append"],
        )
        import_specs = [
            ImportSpec(
                "document.json",
                models.Document,
                importer.import_document,
                import_options,
            ),
            ImportSpec(
                "backgrounds.json",
                models.Background,
                importer.import_background,
                import_options,
            ),
            ImportSpec(
                "classes.json",
                models.CharClass,
                importer.import_class,
                import_options,
                sub_spec=ImportSpec(
                    None, models.Archetype, importer.import_archetype, import_options
                ),
            ),
            ImportSpec(
                "conditions.json",
                models.Condition,
                importer.import_condition,
                import_options,
            ),
            ImportSpec("feats.json", models.Feat, importer.import_feat, import_options),
            ImportSpec(
                "magicitems.json",
                models.MagicItem,
                importer.import_magic_item,
                import_options,
            ),
            ImportSpec(
                "spells.json", models.Spell, importer.import_spell, import_options
            ),
            ImportSpec(
                "monsters.json", models.Monster, importer.import_monster, import_options
            ),
            ImportSpec(
                "planes.json", models.Plane, importer.import_plane, import_options
            ),
            ImportSpec(
                "sections.json", models.Section, importer.import_section, import_options
            ),
            ImportSpec(
                "races.json",
                models.Race,
                importer.import_race,
                import_options,
                sub_spec=ImportSpec(
                    None, models.Subrace, importer.import_subrace, import_options
                ),
            ),
            ImportSpec(
                "weapons.json", models.Weapon, importer.import_weapon, import_options
            ),
            ImportSpec(
                "armor.json", models.Armor, importer.import_armor, import_options
            ),
        ]

        for import_spec in import_specs:
            filepath = directory / import_spec.filename
            if not filepath.exists():
                continue
            md5_hash = _get_md5_hash(filepath)
            importer.ManifestImporter(self.options, filepath, md5_hash)
            with open(filepath, encoding="utf-8") as json_file:
                json_data = json.load(json_file)
            report = importer.import_models_from_json(import_spec, json_data)
            self.stdout.write(self.style.SUCCESS(report))
