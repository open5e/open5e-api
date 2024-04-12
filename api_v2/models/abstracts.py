"""Abstract models to be used in Game Content items."""

from django.db import models
from .enums import MODIFICATION_TYPES


class HasName(models.Model):
    """This is the definition of a name."""

    name = models.CharField(
        max_length=100,
        help_text='Name of the item.')

    def __str__(self):
        return self.name

    class Meta:
        abstract = True


class HasDescription(models.Model):
    """This is the definition of a description."""

    desc = models.TextField(
        help_text='Description of the game content item. Markdown.')

    class Meta:
        abstract = True


class HasPrerequisite(models.Model):
    """This is the definition of a prerequisite."""

    prerequisite = models.CharField(
        max_length=200,
        blank=True,
        help_text='Prerequisite for the game content item.')

    @property
    def has_prerequisite(self):
        return self.prerequisite not in ("", None)

    class Meta:
        abstract = True


class Modification(HasName, HasDescription):
    """
    This is the definition of a modification abstract base class.

    A modification class will be reimplemented from Feat, Race, Background, etc.
    Basically it describes any sort of modification to a character in 5e.
    """


    type = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        choices=MODIFICATION_TYPES,
        help_text='Modification type.')

    class Meta:
        abstract = True
        ordering = ['pk']

class Benefit(HasName, HasDescription):
    class Meta:
        abstract = True
        ordering = ['pk']
