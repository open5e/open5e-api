"""The model for a damage type."""
from django.db import models
from .abstracts import HasName, HasDescription
from .document import FromDocument

class DamageType(HasName, HasDescription, FromDocument):
    """
    This is the model for a damage type.

    Different attacks, damaging spells, and other harmful
    effects deal different types of damage. Damage types
    have no rules of their own, but other rules, such as
    damage resistance, rely on the types.
    """

    class Meta:
        """To assist with the UI layer."""

        verbose_name_plural = "damage types"
