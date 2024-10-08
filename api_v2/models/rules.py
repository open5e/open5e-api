from django.db import models
from .abstracts import HasName, HasDescription, key_field
from .document import FromDocument

class RuleSet(HasName, HasDescription, FromDocument):
  """
  The RuleGroup model contains a set of Rules as part of a larger article, or 
  as a chapter of a book.
  """
  key = key_field()


class Rule(HasName, HasDescription, FromDocument):
  """"
  The Rule model contains information about a single rule from a larger RuleGroup.
  Each Rule is typically a paragraph or two long and might contain tables.
  """

  key = key_field()
  
  index = models.IntegerField(
    default=1,
    help_text="A rule's position in the list of rules of the parent RuleSet"
  )
  
  ruleset = models.ForeignKey(
    RuleSet,
    on_delete=models.CASCADE,
    related_name='rules',
    help_text="The RuleSet which this Rule belongs to"
  )
  
  initialHeaderLevel = models.IntegerField(
    default=1,
    choices=((i, i) for i in range(1,6)),
    help_text="The header level to set rule title to"
  )