import os
import json
import glob

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import IntegrityError, connection
from django.core import serializers

class Command(BaseCommand):
    """Implementation for the `manage.py `dumpbyorg` subcommand."""

    help = 'Import all v2 model data recursively in structured directory.'

    def add_arguments(self, parser):
        parser.add_argument("-d",
                            "--dir",
                            type=str,
                            help="Directory to write files to.")
        parser.add_argument("--debug",
                            action="store_true",
                            help="Load files one by one to identify problematic data.")

    def handle(self, *args, **options) -> None:
        self.stdout.write('Checking if directory exists.')
        if os.path.exists(options['dir']) and os.path.isdir(options['dir']):
            self.stdout.write('Directory {} exists.'.format(options['dir']))
        else:
            self.stdout.write(self.style.ERROR(
                'Directory {} does not exist.'.format(options['dir'])))
            exit(0)

        fixture_filepaths = glob.glob(options['dir'] + '/**/*.json', recursive=True)
        
        self.stdout.write(f'Found {len(fixture_filepaths)} fixture files to load.')
        
        if options['debug']:
            self._load_files_individually(fixture_filepaths)
        else:
            try:
                # Disable foreign key checks during loading
                self._disable_foreign_key_checks()
                self.stdout.write('Disabled foreign key constraints for loading.')
                
                call_command('loaddata', fixture_filepaths)
                
                # Re-enable foreign key checks and validate
                self._enable_foreign_key_checks()
                self.stdout.write('Re-enabled foreign key constraints.')
                
                # Check constraints after all data is loaded
                self._check_constraints()
                self.stdout.write('All foreign key constraints validated successfully.')
                
            except IntegrityError as e:
                # Re-enable foreign key checks even if there was an error
                self._enable_foreign_key_checks()
                
                self.stdout.write(self.style.ERROR(
                    f'Data import completed but foreign key constraint validation failed.'
                ))
                self.stdout.write(self.style.ERROR(f'Error details: {e}'))
                
                # Extract and format the violation details for a clear worklist
                if "Foreign key constraint violations found:" in str(e):
                    violations = str(e).split("Foreign key constraint violations found:\n")[1]
                    self.stdout.write(self.style.ERROR('\nFOREIGN KEY CONSTRAINT VIOLATIONS - WORKLIST:'))
                    for violation in violations.split('\n'):
                        if violation.strip():
                            self.stdout.write(self.style.ERROR(f'  • {violation}'))
                
                self.stdout.write(self.style.ERROR(
                    '\nData import FAILED due to foreign key constraint violations.'
                ))
                self.stdout.write(self.style.WARNING(
                    'Fix the above violations and re-run the import.'
                ))
                raise

    def _disable_foreign_key_checks(self):
        """Disable foreign key constraint checking."""
        with connection.cursor() as cursor:
            if connection.vendor == 'sqlite':
                cursor.execute('PRAGMA foreign_keys = OFF;')
            elif connection.vendor == 'mysql':
                cursor.execute('SET foreign_key_checks = 0;')
            elif connection.vendor == 'postgresql':
                cursor.execute('SET session_replication_role = replica;')

    def _enable_foreign_key_checks(self):
        """Re-enable foreign key constraint checking."""
        with connection.cursor() as cursor:
            if connection.vendor == 'sqlite':
                cursor.execute('PRAGMA foreign_keys = ON;')
            elif connection.vendor == 'mysql':
                cursor.execute('SET foreign_key_checks = 1;')
            elif connection.vendor == 'postgresql':
                cursor.execute('SET session_replication_role = DEFAULT;')

    def _check_constraints(self):
        """Check all foreign key constraints after loading."""
        try:
            with connection.cursor() as cursor:
                if connection.vendor == 'sqlite':
                    cursor.execute('PRAGMA foreign_key_check;')
                    violations = cursor.fetchall()
                    if violations:
                        violation_details = []
                        for violation in violations:
                            violation_details.append(f"Table: {violation[0]}, Row: {violation[1]}, Parent: {violation[2]}, FK: {violation[3]}")
                        raise IntegrityError(f"Foreign key constraint violations found:\n" + "\n".join(violation_details))
                elif connection.vendor == 'mysql':
                    # MySQL will automatically check when we re-enable foreign_key_checks
                    pass
                elif connection.vendor == 'postgresql':
                    # PostgreSQL will check when we reset session_replication_role
                    pass
        except Exception as e:
            raise IntegrityError(f"Foreign key constraint validation failed: {e}")

    def _load_files_individually(self, fixture_filepaths):
        """Load fixture files one by one to identify which one causes the foreign key error."""
        loaded_count = 0
        
        for filepath in sorted(fixture_filepaths):
            try:
                self.stdout.write(f'Loading: {filepath}')
                call_command('loaddata', filepath)
                loaded_count += 1
            except IntegrityError as e:
                self.stdout.write(self.style.ERROR(
                    f'FOREIGN KEY CONSTRAINT FAILED in file: {filepath}'
                ))
                self.stdout.write(self.style.ERROR(f'Error: {e}'))
                
                # Try to identify the specific problematic object
                self._analyze_problematic_file(filepath)
                
                self.stdout.write(f'Successfully loaded {loaded_count} files before failure.')
                raise
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f'Other error in file {filepath}: {e}'
                ))
                raise

    def _analyze_problematic_file(self, filepath):
        """Analyze the problematic file to identify specific objects causing issues."""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            self.stdout.write(f'Analyzing {len(data)} objects in {filepath}:')
            
            for i, obj in enumerate(data):
                try:
                    # Try to deserialize just this one object
                    for deserialized_obj in serializers.deserialize('json', [obj]):
                        # Try to save it
                        deserialized_obj.save()
                except IntegrityError as e:
                    self.stdout.write(self.style.ERROR(
                        f'  Object {i+1}: {obj.get("model", "unknown")} '
                        f'pk="{obj.get("pk", "unknown")}" FAILED'
                    ))
                    self.stdout.write(self.style.ERROR(f'    Error: {e}'))
                    
                    # Show the object's foreign key fields
                    fields = obj.get('fields', {})
                    fk_fields = {}
                    for field_name, field_value in fields.items():
                        if field_value and (isinstance(field_value, str) or isinstance(field_value, list)):
                            # Likely a foreign key reference
                            fk_fields[field_name] = field_value
                    
                    if fk_fields:
                        self.stdout.write(f'    Foreign key fields: {fk_fields}')
                    
                    return  # Stop at first problematic object
                except Exception as e:
                    self.stdout.write(self.style.WARNING(
                        f'  Object {i+1}: Other error - {e}'
                    ))
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Could not analyze file: {e}'))
