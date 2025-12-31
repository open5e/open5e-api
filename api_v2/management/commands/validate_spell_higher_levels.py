"""
Management command to validate that all spells with "higher_level" text
have corresponding SpellCastingOption entries.
"""
import json
import glob
from pathlib import Path

from django.core.management.base import BaseCommand

# Maximum length for truncated text in output
MAX_DESCRIPTION_LENGTH = 100


class Command(BaseCommand):
    """Validate that spells with higher_level text have casting options."""

    help = 'Validate that all spells with "At Higher Levels" descriptions have corresponding casting options.'

    def add_arguments(self, parser):
        parser.add_argument(
            "-d",
            "--dir",
            type=str,
            default="data/v2",
            help="Directory to search for spell data files (default: data/v2)."
        )

    def handle(self, *args, **options):
        """Check all spell files for missing casting options."""
        base_dir = options['dir']
        
        if not Path(base_dir).exists():
            self.stdout.write(self.style.ERROR(
                f'Directory {base_dir} does not exist.'
            ))
            return

        self.stdout.write(f'Checking spell data in {base_dir}...')
        
        # Find all Spell.json and SpellCastingOption.json files
        spell_files = glob.glob(f'{base_dir}/**/Spell.json', recursive=True)
        option_files = glob.glob(f'{base_dir}/**/SpellCastingOption.json', recursive=True)
        
        self.stdout.write(f'Found {len(spell_files)} Spell.json files')
        self.stdout.write(f'Found {len(option_files)} SpellCastingOption.json files')
        
        total_issues = 0
        total_spells_checked = 0
        
        # Process each spell file
        for spell_file in sorted(spell_files):
            # Get the corresponding casting option file
            option_file = spell_file.replace('Spell.json', 'SpellCastingOption.json')
            
            # Load spells
            with open(spell_file, 'r') as f:
                spells = json.load(f)
            
            # Load casting options if the file exists
            casting_options = []
            if Path(option_file).exists():
                with open(option_file, 'r') as f:
                    casting_options = json.load(f)
            
            # Create a set of spell PKs that have casting options
            spells_with_options = set()
            for opt in casting_options:
                parent = opt.get('fields', {}).get('parent')
                if parent:
                    spells_with_options.add(parent)
            
            # Check each spell
            issues_in_file = []
            for spell in spells:
                total_spells_checked += 1
                pk = spell.get('pk')
                name = spell.get('fields', {}).get('name', 'Unknown')
                level = spell.get('fields', {}).get('level', '?')
                higher_level = spell.get('fields', {}).get('higher_level', '')
                
                # Check if spell has higher_level text but no casting options
                if higher_level.strip() and pk not in spells_with_options:
                    issues_in_file.append({
                        'name': name,
                        'pk': pk,
                        'level': level,
                        'higher_level': higher_level
                    })
                    total_issues += 1
            
            # Report issues for this file
            if issues_in_file:
                self.stdout.write(self.style.WARNING(
                    f'\n{spell_file}:'
                ))
                for issue in issues_in_file:
                    self.stdout.write(self.style.ERROR(
                        f'  ✗ {issue["name"]} (level {issue["level"]}, pk: {issue["pk"]})'
                    ))
                    # Truncate description if needed
                    desc = issue["higher_level"]
                    if len(desc) > MAX_DESCRIPTION_LENGTH:
                        desc = desc[:MAX_DESCRIPTION_LENGTH] + '...'
                    self.stdout.write(f'    Higher Level: {desc}')
        
        # Final report
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(f'Validation complete:')
        self.stdout.write(f'  Total spells checked: {total_spells_checked}')
        
        if total_issues == 0:
            self.stdout.write(self.style.SUCCESS(
                f'  ✓ All spells with "higher_level" text have casting options!'
            ))
        else:
            self.stdout.write(self.style.ERROR(
                f'  ✗ {total_issues} spell(s) missing casting options'
            ))
            self.stdout.write(self.style.WARNING(
                '\nPlease add SpellCastingOption entries for the spells listed above.'
            ))
