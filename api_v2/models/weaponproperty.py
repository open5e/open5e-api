from .abstracts import HasName, HasDescription
from .document import FromDocument

class WeaponProperty(HasName, FromDocument, HasDescription):  
  class Meta:
      verbose_name_plural = "Weapon Properties"