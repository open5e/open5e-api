"""
The model for abilities.

Includes descriptions for each ability type.
"""

from django.db import models
from django.core.validators import MinValueValidator

from .abstracts import HasName, HasDescription
from .document import FromDocument

class Ability(HasName, FromDocument):
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

    @property
    def descriptions(self):
        """ Gets the description based on parameter, and then if none, global priority"""
        return AbilityDescription.objects.filter(describes=self).all()


class AbilityDescription(HasDescription, FromDocument):
    """A description of the ability"""
    describes = models.ForeignKey(Ability, on_delete=models.CASCADE)


class Skill(HasName, FromDocument):
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

    @property
    def descriptions(self):
        """ Gets the description based on parameter, and then if none, global priority"""
        return SkillDescription.objects.filter(describes=self).all()


class SkillDescription(HasDescription, FromDocument):
    """A description of the skill"""
    describes = models.ForeignKey(Skill, on_delete=models.CASCADE)
