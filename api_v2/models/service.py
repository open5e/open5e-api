from django.db import models
from .abstracts import HasName, HasDescription, HasPrice
from .document import FromDocument


class Service(HasDescription, FromDocument, HasPrice):
  """
  
  This is the Model for a purchasable Service

  This is a companion model to Item for those purchasable services that aren't
  actually Items; life style expenses, hireling, etc.

  """
  # 'name', 'document', 'cost' fields inherited from abstract classes

  detail = models.TextField(
    null=True,
    blank=True,
    help_text="Additional contextual infomation about the service. ie. For 'Squalid Living' the detail would be '1 day'"
  )