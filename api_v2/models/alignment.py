"""The model for an alignment."""

from django.db import models

from .abstracts import HasName, HasDescription
from .document import FromDocument


class Alignment(HasName, HasDescription, FromDocument):
    """This is the model for an alignment, which is way to describe the 
    moral and personal attitudes of a creature."""

