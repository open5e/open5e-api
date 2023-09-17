"""The model for a feat."""
from django.db import models
from .abstracts import HasName, HasDescription, Benefit
from .document import FromDocument


class BackgroundBenefit(Benefit):
    background = models.ForeignKey('Background', on_delete=models.CASCADE)

class Characteristics(models.Model):
    """This is the model for suggested characteristics for a background."""
    background = models.OneToOneField('Background', on_delete=models.CASCADE)

    personality_trait_table = models.TextField(
        help_text="Table to roll for personality traits. Markdown."
    )
    ideal_table = models.TextField(
        help_text="Table to roll for ideals. Markdown."
    )
    bond_table = models.TextField(
        help_text="Table to roll for bonds. Markdown."
    )
    flaw_table = models.TextField(
        help_text="Table to roll for flaws. Markdown."
    )


class BackgroundFeature(HasName, HasDescription):
    background = models.OneToOneField('Background', on_delete=models.CASCADE)


class Background(HasName, HasDescription, FromDocument):
    """
    This is the model for a character background.

    Your character's background reveals where you came from, how you became
    an adventurer, and your place in the world.
    """

    #skills = models.ForeignKey('Benefit')
    # 
    # tools - item_set
    # languages - language_set
    # equipment - FK to itemset?

    #    characteristics = 

    class Meta:
        """To assist with the UI layer."""

        verbose_name_plural = "backgrounds"
