"""
The model for abilities.

Includes descriptions for each ability type.
"""

from django.db import models
from django.core.validators import MinValueValidator

from .abstracts import HasName, HasDescription
from .document import FromDocument

class Ability(HasName, HasDescription, FromDocument):
    """
    This is the definition of the Ability class.
    """

    short_desc = models.CharField(
        max_length=100,
        help_text='Short description of the ability.')

    @property
    def skills(self):
        return self.skill_set.all()

    class Meta:
        """To assist with the UI layer."""

        verbose_name_plural = "abilities"


class Skill(HasName, HasDescription, FromDocument):
    """
    This is the definition of the skill class.
    """

    ability = models.ForeignKey(
        Ability,
        on_delete=models.CASCADE,
        help_text='The ability referenced by this skill.'
    )

    class Meta:
        """To assist with the UI layer."""

        verbose_name_plural = "skills"
