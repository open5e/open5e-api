"""
Management command to populate concept objects by grouping equivalent content across game systems.

This command analyzes existing content objects and groups them by name to create
concept objects that represent the same conceptual item across different game systems.

Currently supports:
- ConditionConcept (for Condition objects)

This can be extended to support other content types like SpellConcept, ItemConcept, etc.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify
from collections import defaultdict

from api_v2.models import Condition, ConditionConcept


class Command(BaseCommand):
    help = 'Populate concept objects by grouping equivalent content across game systems'

    def handle(self, *args, **options):
        self.populate_condition_concepts()
        
        # Future content types can be added here:
        # self.populate_damage_type_concepts()
        # self.populate_environment_concepts()

    def populate_condition_concepts(self):
        """Populate ConditionConcept objects by grouping equivalent conditions."""
        self.stdout.write(self.style.HTTP_INFO('Processing conditions...'))
        
        # Always clear existing concepts and reconstruct
        self.stdout.write('Clearing existing ConditionConcept objects...')
        ConditionConcept.objects.all().delete()

        # Group conditions by exact name (no normalization needed)
        condition_groups = defaultdict(list)
        
        for condition in Condition.objects.all():
            condition_groups[condition.name].append(condition)

        self.stdout.write(f'Found {len(condition_groups)} condition concepts to create:')

        created_count = 0
        
        with transaction.atomic():
            for concept_name, conditions in condition_groups.items():
                concept_key = slugify(concept_name)
                
                # Create description based on number of systems
                systems = list(set([c.document.gamesystem.name for c in conditions]))
                if len(systems) == 1:
                    concept_desc = f"The {concept_name.lower()} condition from {systems[0]}."
                else:
                    concept_desc = f"The {concept_name.lower()} condition as it appears across different game systems: {', '.join(systems)}."
                
                self.stdout.write(f'  - {concept_name} ({concept_key}): {len(conditions)} conditions across {len(systems)} systems')
                
                # Create the ConditionConcept
                concept = ConditionConcept.objects.create(
                    key=concept_key,
                    name=concept_name,
                    desc=concept_desc
                )
                
                # Add all conditions to this concept
                concept.conditions.set(conditions)
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} ConditionConcept objects'))

 