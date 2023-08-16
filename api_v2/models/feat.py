"""The model for a feat."""
from django.db import models
from .abstracts import HasName, HasDescription, HasPrerequisite
from .document import FromDocument


class Feat(HasName, HasDescription, HasPrerequisite, FromDocument):
    """
    This is the model for a feat.

    A feat represents a talent or an area of expertise that
    gives a character special capabilities. It embodies
    training, experience, and abilities beyond what a
    class provides.
    """

    class Meta:
        """To assist with the UI layer."""

        verbose_name_plural = "feats"

