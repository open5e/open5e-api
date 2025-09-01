"""The model for a damage type."""
from django.db import models
from .abstracts import HasName, HasDescription
from .document import FromDocument

class DamageType(HasName, FromDocument):
    """
    This is the model for a damage type.

    Different attacks, damaging spells, and other harmful
    effects deal different types of damage. Damage types
    have no rules of their own, but other rules, such as
    damage resistance, rely on the types.
    """
    @property
    def get_desc(self):
        """ Gets the description based on parameter, and then if none, global priority"""
        return DamageTypeDescription.objects.filter(describes=self).first()

    class Meta:
        """To assist with the UI layer."""

        verbose_name_plural = "damage types"


class DamageTypeDescription(HasDescription, FromDocument):
    describes = models.ForeignKey(DamageType, on_delete=models.CASCADE)
