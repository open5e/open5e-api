"""The model for an alignment."""

from django.db import models

from .abstracts import HasName, HasDescription
from .document import FromDocument


class Alignment(HasName, HasDescription, FromDocument):
    """This is the model for an alignment, which is way to describe the 
    moral and personal attitudes of a creature."""

    @property
    def short_name(self):
        short_name = ""
        for word in self.name.split(" "):
            short_name += word[0].upper()
        return short_name

    @property
    def morality(self):
        return self.name.split(" ")[-1].lower()

    @property
    def societal_attitude(self):
        return self.name.split(" ")[0].lower()
