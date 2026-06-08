"""The model for a feat."""
from django.db import models
from .abstracts import HasName, HasDescription, HasPrerequisite, Modification, key_field
from .document import FromDocument

FEAT_TYPES = [
    ('GENERAL', 'General'),
    ('ORIGIN', 'Origin'),
    ('FIGHTING_STYLE', 'Fighting Style'),
    ('EPIC_BOON', 'Epic Boon'),
    ('General', 'General'),
    ('Origin', 'Origin'),
    ('Fighting Style', 'Fighting Style'),
    ('Epic Boon', 'Epic Boon'),
]

class FeatBenefit(Modification):
    """This is the model for an individual benefit of a feat."""
    key = key_field()
    parent = models.ForeignKey('Feat', on_delete=models.CASCADE)
    order = models.SmallIntegerField(
        blank=True,
        null=True,
        help_text='The position in the list of features that this feature appears in its source statblock'
    )

    class Meta:
        ordering = ['parent', 'order']


class Feat(HasName, HasDescription, HasPrerequisite, FromDocument):
    """
    This is the model for a feat.

    A feat represents a talent or an area of expertise that
    gives a character special capabilities. It embodies
    training, experience, and abilities beyond what a
    class provides.
    """

    type = models.CharField(
        max_length=32,
        choices=FEAT_TYPES,
        default='GENERAL'
    )

    @property
    def benefits(self):
        """Returns the set of benefits that are related to this feat."""
        return self.featbenefit_set

    class Meta:
        """To assist with the UI layer."""

        verbose_name_plural = "feats"
