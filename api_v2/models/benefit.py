from django.db import models
from .abstracts import HasName, HasDescription, HasPrerequisite


class Benefit(HasName, HasDescription):
    """
    This is the model for a benefit.
    
    Benefits can be many different types, and should be used as the default
    data type to describe something that modifies a character.
    """

    