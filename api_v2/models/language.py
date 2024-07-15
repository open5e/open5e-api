"""The model for a language."""

from django.db import models

from .abstracts import HasName, HasDescription
from .abstracts import distance_field
from .document import FromDocument


class Language(HasName, HasDescription, FromDocument):
    """This is the model for a language, which is a form of communication."""

    script_language = models.ForeignKey('self',
                                        null=True,
                                        blank=True,
                                        on_delete=models.CASCADE)

    # TODO typical_speakers will be a FK out to a Creature Types table.

    is_exotic = models.BooleanField(
        help_text='Whether or not the language is exotic.',
        default=False)

    is_secret = models.BooleanField(
        help_text='Whether or not the language is secret.',
        default=False)

class HasLanguage(models.Model):
    """The abstract class used by Creature to describe what a creature's language."""
    languages_desc = models.TextField(
        blank=True,
        default="[None provided]",
        help_text='Description of the languages item.')

    languages = models.ManyToManyField(Language)
    telepathy_range = distance_field()
    class Meta:
        abstract = True