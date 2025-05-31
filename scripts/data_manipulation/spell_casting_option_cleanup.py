from api_v2 import models as v2

def main():
    total_empties=0
    for sco in v2.SpellCastingOption.objects.all():
        if sco.type=='default': continue
        if sco.type=='ritual': continue
        if sco.damage_roll is not None: continue
        if sco.target_count is not None: continue
        if sco.duration is not None: continue
        if sco.range is not None: continue
        if sco.concentration is not None: continue
        if sco.shape_size is not None: continue
        print("Found an empty one at {}".format(sco.id))
        total_empties+=1
        sco.delete()
        
    print(total_empties)

if __name__ == '__main__': main()