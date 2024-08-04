'''The abstract model related to the Speed concept in 5e.'''

from django.db import models
from .abstracts import distance_field, distance_unit_field

class HasSpeed(models.Model):
    '''This object represents a creature's speed.'''

    walk = distance_field(null=False)
    unit = distance_unit_field()
    hover = models.BooleanField(
        default=False,
        null=False,
        help_text="Whether or not the walk movement is hovering."
    )
    fly = distance_field(null=True)
    burrow = distance_field(null=True)
    climb = distance_field(null=True)
    swim = distance_field(null=True)

    def get_fly(self):
        if self.fly is None:
            return 0.0
        return self.fly

    def get_burrow(self):
        if self.burrow is None:
            return 0.0
        return self.burrow
    
    def get_climb(self):
        if self.climb is None:
            return self.walk / 2 # Climb speed is half of walk speed.
        return self.climb

    def get_crawl(self):
        return self.walk / 2

    def get_swim(self):
        if self.swim is None:
            return self.walk / 2 # Swim speed is half of walk speed.
        return self.swim

    def get_unit(self):
        if self.unit is None:
            return self.document.distance_unit
        return self.unit

    def get_speed(self):
        speed={
            "walk":self.walk,
            "unit":self.get_unit(),
            "fly":self.fly,
            "burrow":self.burrow,
            "climb":self.climb,
            "swim":self.swim,
        }
        if self.hover:
            speed['hover']=True # Hover field not present unless true.
        
        return speed

    def get_speed_all(self):
        return {
            "unit": self.get_unit(),
            "walk": self.walk,
            "crawl": self.get_crawl(),
            "hover": self.hover,
            "fly": self.get_fly(),
            "burrow": self.get_burrow(),
            "climb": self.get_climb(),
            "swim": self.get_swim()
        }
        

    class Meta:
        abstract = True
