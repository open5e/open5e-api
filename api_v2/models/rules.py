from django.db import models
from .abstracts import HasName, HasDescription, key_field
from .document import FromDocument


# TODO it has been agreed that this model should be called 'RuleSet' and that 
# existant the 'RuleSet' should be renamed to 'GameSystem'.
#
# This change be handled in its own PR, as it represents a significant 
# expansion of the initial issue and will likely touch many files, causing 
# headaches for whichever poor soul ends up reviewing it

class RuleGroup(HasName, HasDescription, FromDocument):
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
  index = models.IntegerField(default=1)
  ruleset = models.ForeignKey(
    RuleGroup,
    on_delete=models.CASCADE,
    related_name='rules'
  )
  
  initialHeaderLevel = models.IntegerField(
    default=1,
    choices=((i, i) for i in range(1,6))
  )