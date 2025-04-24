
from django.template.defaultfilters import slugify

import json

from api_v2 import models as v2_models

from api import models as v1_models





def main():
    for sl in v1_models.SpellList.objects.all():
        v2_class_key = "srd_"+sl.pk
        v2_class = v2_models.CharacterClass.objects.get(pk=v2_class_key)
        
        for s in sl.spells.all():
            prefixes = ['srd_','deepm_','deepmx_']
            for prefix in prefixes:
                try:
                    v2_spell = v2_models.Spell.objects.get(pk=prefix+s.pk)
                except:
                    pass
                    #print("couldn't find {}".format(prefix+s.pk))
            
            v2_spell.classes.add(v2_class)
            v2_spell.full_clean()





if __name__ == '__main__':
    main()