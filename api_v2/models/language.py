"""The model for a language."""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse

from api.models import GameContent
from .weapon import Weapon
from .armor import Armor
from .abstracts import Object, HasName, HasDescription
from .document import FromDocument


class Language(HasName, HasDescription, FromDocument):
    """This is the model for a language, which is a form of communication."""

    script_language = models.ForeignKey('self',
                                        null=True,
                                        on_delete=models.CASCADE)

    # TODO typical_speakers will be a FK out to a Creature Types table.

    is_exotic = models.BooleanField(
        help_text='Whether or not the language is exotic.',
        default=False)

    is_secret = models.BooleanField(
        help_text='Whether or not the language is secret.',
        default=False)
