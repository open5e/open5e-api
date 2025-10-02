"""The model for a species, sub-species, and it's traits."""

from django.db import models
from .abstracts import HasName, HasDescription, HasPrerequisite, Modification, key_field
from .document import FromDocument
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes

class SpeciesTrait(Modification):
    """This is the model for a species or sub-species trait.

    It inherits from modification, which is an abstract concept.
    """
    key = key_field()
    parent = models.ForeignKey('Species', on_delete=models.CASCADE)

    SPECIES_FEATURE_TYPES = [
        ('ABILITY_MODS', 'ABILITY_MODS'),
        ('SIZE', 'SIZE'),
        ('SPEED', 'SPEED'),
    ]

    type = models.CharField(
        blank=True,
        null=True,
        max_length=16,
        choices=SPECIES_FEATURE_TYPES,
    )

    order = models.SmallIntegerField(
        blank=True,
        null=True,
        help_text='The position in the list of features that a feature appears in its source statblock'
    )

class Species(HasName, HasDescription, FromDocument):
    """
    This is the model for a species or sub-species.

    This model can be used to represent species and sub-species. Sub-species are
    represented by using a self-relation to the parent species.
    """

    subspecies_of = models.ForeignKey('self',
                                   default=None,
                                   blank=True,
                                   null=True,
                                   on_delete=models.CASCADE)

    @property
    @extend_schema_field(OpenApiTypes.BOOL)
    def is_subspecies(self):
        """Returns whether the object is a subspecies."""
        return self.subspecies_of is not None

    @property
    def traits(self):
        """Returns the set of traits that are related to this species."""
        return self.speciestrait_set

    def search_result_extra_fields(self):
        return {
            "subspecies_of": { 
                "name": self.subspecies_of.name,
                "key": self.subspecies_of.key
            } if self.subspecies_of else None
        }
    class Meta:
        """To assist with the UI layer."""

        verbose_name_plural = "species"
