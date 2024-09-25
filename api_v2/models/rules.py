from django.db import models
from .abstracts import HasName, HasDescription, key_field

class Rule(HasName, HasDescription):
  """"
  This Model is used to represent game content in the form of rules and 
  articles.
  """
  key = key_field()

  next = models.ForeignKey(
    'self',
    blank=True,
    null=True,
    on_delete=models.SET_NULL,
    related_name="previous"
  )
  
  initialHeaderLevel = models.IntegerField(
    default=1,
    choices=((i, i) for i in range(1,6))
  )