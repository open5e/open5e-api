from django.db import models

from .models import GameContent


class Spell(GameContent):

    spell_level_name_lookup = [
        'Cantrip',
        '1st-level',
        '2nd-level',
        '3rd-level',
        '4th-level',
        '5th-level',
        '6th-level',
        '7th-level',
        '8th-level',
        '9th-level'
    ]

    school_options = [
        'abjuration',
        'conjuration',
        'divination',
        'enchantment',
        'evocation',
        'illusion',
        'necromancy',
        'transmutation'
    ]

    area_of_effect_shape_options = [
        'cone',
        'cube',
        'cylinder',
        'line',
        'sphere'
    ]

    damage_types = [
        'acid',
        'cold',
        'fire',
        'force',
        'lightning',
        'necrotic',
        'poison',
        'psychic',
        'radiant',
        'thunder'
    ]

    higher_level = models.TextField(
        help_text='What happens if you cast this at a higher level.')
    page = models.TextField(
        help_text='Page number reference for the document.')
    
    range = models.TextField(help_text='Text description of the range.')
    target_range_sort = models.IntegerField(help_text='Sortable distance ranking to the target.')

    components = models.TextField(
        help_text='Single-character list of V, S, M for Verbal, Somatic, or Material based on the spell requirements.')
    material = models.TextField(
        help_text='Description of the material required.')
    
    can_be_cast_as_ritual = models.BooleanField(
        help_text='Whether or not the spell can be cast as a ritual.')
    # Maintaining compatibility with the old "ritual" string field.
    def v1_ritual(self):
        if self.can_be_cast_as_ritual:
            return "yes"
        else:
            return "no"
    
    duration = models.TextField(
        help_text='Description of the duration such as "instantaneous" or "Up to 1 minute"')
    
    requires_concentration = models.BooleanField(
        help_text='Whether the spell requires concentration')
    # Maintaining compatibility with the old "concentration" string field
    def v1_concentration(self):
        if self.requires_concentration:
            return "yes"
        else:
            return "no"

    casting_time = models.TextField(
        help_text='Amount of time it takes to cast the spell, such as "1 bonus action" or "4 hours".')
    
    
    spell_level = models.IntegerField(
        help_text='Integer representing the level of the spell. Cantrip is 0.')
    # Maintaining compatibility with the old string field.
    def v1_level(self):
        return self.spell_level_name_lookup[self.spell_level]

    school = models.TextField(
        help_text='Representation of the school of magic, such as "illusion" or "evocation".')
    dnd_class = models.TextField(
        help_text='List of classes (comma separated) that can learn this spell.')
    archetype = models.TextField(
        help_text='Archetype that can learn this spell. If empty, assume all archetypes.')
    circles = models.TextField(
        help_text='Druid Archetypes that can learn this spell.')
    route = models.TextField(default="spells/")

    @staticmethod
    def plural_str() -> str:
        """Return a string specifying the plural name of this model."""
        return "Spells"
