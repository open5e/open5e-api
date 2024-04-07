"""
The model for a spell.

Also includes importing and some presentation logic.
"""

from django.db import models
from django.template.defaultfilters import slugify
from django.core.validators import MinValueValidator
from django.core.validators import MaxValueValidator

from .models import GameContent
from ..validators import spell_school_validator


class Spell(GameContent):
    """The model for a spell."""

    # Stored metadata about the spell
    page = models.TextField(
        help_text='Page number reference for the document.')

    spell_level = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(9)],
        help_text='Integer representing the level of the spell. Cantrip is 0.')

    dnd_class = models.TextField(
        help_text='List of classes (comma separated) that can learn this spell.')

    school = models.TextField(
        validators = [spell_school_validator],
        help_text='Representation of the school of magic, such as "illusion" or "evocation".')

    # Computed metadata about the spell
    def v1_level(self):
        """Presents the spell level in a friendly format."""
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
        return spell_level_name_lookup[self.spell_level]

    # Stored data about casting the spell
    casting_time = models.TextField(
        help_text='Amount of time it takes to cast the spell, such as "1 bonus action" or "4 hours".')

    range = models.TextField(help_text='Text description of the target range.')

    target_range_sort = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text='Sortable distance ranking to the target. 0 for self, 1 for touch, sight is 9999, unlimited (same plane) is 99990, unlimited any plane is 99999. All other values in feet.')

    requires_verbal_components = models.BooleanField(
        help_text='Casting this spell requires verbal components.',
        default=False)
    requires_somatic_components = models.BooleanField(
        help_text='Casting this spell requires somatic components.',
        default=False)
    requires_material_components = models.BooleanField(
        help_text='Casting this spell requires material components.',
        default=False)

    material = models.TextField(
        help_text='Description of the material required.')

    higher_level = models.TextField(
        help_text='What happens if you cast this at a higher level.')

    can_be_cast_as_ritual = models.BooleanField(
        help_text='Whether or not the spell can be cast as a ritual.',
        default=False)

    # Computed data about casting the spell
    def v1_components(self):
        """Presents the components in a standard list like "V, S, M" """
        components_list = []
        if self.requires_verbal_components:
            components_list.append("V")
        if self.requires_somatic_components:
            components_list.append("S")
        if self.requires_material_components:
            components_list.append("M")

        return ', '.join(components_list)

    def v1_ritual(self):
        """Field calculated and presented to maintain compatibility with original API."""
        if self.can_be_cast_as_ritual:
            return "yes"
        else:
            return "no"

    # Stored data about the spell's effect
    duration = models.TextField(
        help_text='Description of the duration such as "instantaneous" or "Up to 1 minute"')

    requires_concentration = models.BooleanField(
        help_text='Whether the spell requires concentration',
        default=False)

    def v1_concentration(self):
        """Field calculated and presented to maintain compatibility with original API."""
        if self.requires_concentration:
            return "yes"
        else:
            return "no"

    archetype = models.TextField(
        help_text='Archetype that can learn this spell. If empty, assume all archetypes.')
    circles = models.TextField(
        help_text='Druid Archetypes that can learn this spell.')
    route = models.TextField(default="spells/")

    def import_from_json_v1(self, json):
        """Logic to import from the v1 file spec."""
        self.name = json["name"]
        self.slug = json.get("slug", slugify(json["name"]))
        if "desc" in json:
            self.desc = json["desc"]
        if "higher_level" in json:
            self.higher_level = json["higher_level"]
        if "page" in json:
            self.page = json["page"]
        # Logic to set an integer based on v1 file import spec (a string).
        if "range" in json:
            # If the spell range includes an effect description like "(10 ft
            # cube)", remove.
            range_trimmed = str(json['range'].split(" (")[0]).lower()

            # Set target range sort based on the following rules:
            # Self = 0
            # Touch = 1
            # Any other distance is recorded in feet.
            # "Sight" is recorded as 9999
            # Unlimited (same-plane) is recorded as 99990
            # Unlimited (multi-plane) is recorded as 99999

            if 'self' in range_trimmed:
                # Various spells in deep magic include effect shape.
                self.target_range_sort = 0
            if range_trimmed == 'touch':
                self.target_range_sort = 1

            if range_trimmed == 'sight':
                self.target_range_sort = 9999

            if range_trimmed == 'unlimited':
                self.target_range_sort = 99999

            if range_trimmed == 'special':
                # For now, assume it's single plane
                self.target_range_sort = 99990

            if range_trimmed.endswith(
                    'miles') or range_trimmed.endswith('mile'):
                # Assume it's in the format "xx Miles"
                miles = int(json['range'].split(" ")[0])
                self.target_range_sort = miles * 5280

            if range_trimmed.endswith('feet') or range_trimmed.endswith('ft.'):
                # Assume it's in the format "xx Miles"
                feet = int(range_trimmed.split(" ")[0])
                self.target_range_sort = feet

            self.range = json["range"]
        if "components" in json:
            # These fields default to False, and then set to true based on string of
            # "V, S, M"
            if 'v' in json['components'].lower():
                self.requires_verbal_components = True
            if 's' in json['components'].lower():
                self.requires_somatic_components = True
            if 'm' in json['components'].lower():
                self.requires_material_components = True

        if "material" in json:
            self.material = json["material"]

        # Logic to set boolean based on v1 file import spec (a string).
        if "ritual" in json:
            # Default is false
            if str(json["ritual"]).lower() == 'yes':
                self.can_be_cast_as_ritual = True

            if str(json["ritual"]).lower() == 'no':
                pass  # Already set as False through default.

        if "duration" in json:
            self.duration = json["duration"]

        # Logic to set a boolean based on v1 file import spec (a string).
        if "concentration" in json:
            if str(json["concentration"]).lower() == 'yes':
                self.requires_concentration = True

        if "casting_time" in json:
            self.casting_time = json["casting_time"]
        if "level" in json:
            self.level = json["level"]

        # Model field is renamed to spell_level
        if "level_int" in json:
            self.spell_level = json["level_int"]

        if "school" in json:
            self.school = json["school"]
        if "class" in json:
            self.dnd_class = json["class"]
        if "archetype" in json:
            self.archetype = json["archetype"]
        if "circles" in json:
            self.circles = json["circles"]

    @staticmethod
    def plural_str() -> str:
        """Return a string specifying the plural name of this model."""
        return "Spells"

    def search_result_extra_fields(self):
        return {
            "school":self.school,
            "dnd_class":self.dnd_class}



class SpellList(GameContent):
    """ A list of spells to be referenced by classes and subclasses"""
    
    spells = models.ManyToManyField(Spell,
        related_name="spell_lists",
        help_text='The set of spells.')

    def import_from_json_v1(self, json):
        """Log to import a single object from a standard json structure."""
        self.name = json["name"]
        self.slug = slugify(json["name"])
        if "desc" in json:
            self.desc = json["desc"]

        for spell_slug in json["spell_list"]:
            #spell_obj = Spell.objects.filter(slug=spell_slug)
            self.spells.add(spell_slug)


    @staticmethod
    def plural_str() -> str:
        """Return a string specifying the plural name of this model."""
        return "SpellLists"

