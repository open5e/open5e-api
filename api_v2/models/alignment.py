"""The model for an alignment."""

from django.db import models

from .abstracts import HasName, HasDescription
from .document import FromDocument
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes

class Alignment(HasName, HasDescription, FromDocument):
    """This is the model for an alignment, which is way to describe the 
    moral and personal attitudes of a creature."""

    @property
    @extend_schema_field(OpenApiTypes.STR)
    def short_name(self):
        short_name = ""
        for word in self.name.split(" "):
            short_name += word[0].upper()
        return short_name

    @property
    @extend_schema_field(OpenApiTypes.STR)
    def morality(self):
        return self.name.split(" ")[-1].lower()

    @property
    @extend_schema_field(OpenApiTypes.STR)
    def societal_attitude(self):
        return self.name.split(" ")[0].lower()
