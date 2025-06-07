"""The model for a condition."""
from django.db import models
from django.db.models import Q

from .abstracts import HasName, HasDescription
from .document import FromDocument
from .image import HasIcon

class Condition(HasName, HasDescription, HasIcon, FromDocument):
    """
    This is the model for a condition.
    """

    class Meta:
        """To assist with the UI layer."""

        verbose_name_plural = "conditions"


class ConditionConcept(HasName, HasDescription):
    """
    This model represents a synthetic condition concept that aggregates
    equivalent conditions across different game systems.
    
    For example, "Invisible" may exist in multiple game systems (SRD 2014, A5e, etc.)
    but conceptually they represent the same condition. This model provides a 
    unified view of that concept with links to all its implementations.
    """
    
    key = models.CharField(
        primary_key=True,
        max_length=100,
        help_text="Unique key for the condition concept (e.g., 'invisible')."
    )
    
    conditions = models.ManyToManyField(
        Condition,
        related_name='concepts',
        help_text="All condition implementations that are equivalent to this concept."
    )
    
    @property
    def gamesystems(self):
        """Returns a list of all game systems that have this condition concept."""
        return list(set([condition.document.gamesystem for condition in self.conditions.all()]))
    
    @property
    def documents(self):
        """Returns a list of all documents that have this condition concept."""
        return list(set([condition.document for condition in self.conditions.all()]))
    
    def get_condition_for_gamesystem(self, gamesystem_key):
        """
        Returns the condition for a specific game system.
        If multiple conditions exist for the same game system, returns the first one.
        """
        return self.conditions.filter(document__gamesystem__key=gamesystem_key).first()
    
    def get_condition_for_document(self, document_key):
        """Returns the condition for a specific document."""
        return self.conditions.filter(document__key=document_key).first()
    
    class Meta:
        verbose_name = "condition concept"
        verbose_name_plural = "condition concepts"
        ordering = ['name']
