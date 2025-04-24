from django.template.defaultfilters import slugify

import json
import csv

from api.models import Document as Document1
from api_v2.models import Document as Document2
from api_v2.models import Creature
from api_v2.models import Environment

def main():
    #file = "./scripts/data_manipulation/monsters - 5.1 SRD.csv"
    file= "./scripts/data_manipulation/merged.json"
    #doc_key = "tob2"
    unfound=0


    with open(file, 'r', encoding='utf-8') as f:
        #monsters = csv.DictReader(f)
        monsters = json.load(f)

        for monster in monsters:
            #for n in range(0,20):
            #    ename = "environments/{}".format(n)
            if 'environments' in monster:
                for ename in monster.get('environments'):
                    #if monster[ename] is not None and monster[ename] != "":
                        #print(monster['name'],monster[ename])
                        docv1 = Document1.objects.get(slug=monster['document__slug'])
                        docv2 = Document2.objects.get(pk=docv1.v2_related_key)
                        creature_key = "{}_{}".format(docv2.key, slugify(monster['name']))
                        env = slugify(ename)
                        #print("{} {}".format(creature_key, env))
                        try:
                            cobj = Creature.objects.get(key=creature_key)
                        except:
                            print("Creature {} matching query does not exist.".format(creature_key))
                        e = get_env(env, doc_key=docv2.key)
                        if creature_key == "ccdx_pech":
                            e = get_env('plane-of-earth','srd')
                        if creature_key == "tob_valkyrie":
                            e = get_env('elysium','srd')
                        if e is None:
                            if env == 'any':
                                for e_obj in Environment.objects.all():
                                    cobj.environments.add(e_obj)
                                    pass
                            else:
                                
                                unfound+=1
                                print("Couldn't find {} {}".format(env, creature_key))
                        else:
                            cobj.environments.add(e)
                            pass
                            #Map e to creature.

    print("{} unfound environemnts.".format(unfound))

def get_env(env_name, doc_key):
    synonyms={
        "coastal":"coast",
        "hill":"hills",
        "mountains":"mountain",
        "plains":"grassland",
        "plain":"grassland",
        "caverns":"caves",
        "underdark":"underworld",
        "volcano":"mountain",
        "settlement":"urban",
        "jungle":"forest",
        "tundra":"arctic",
        "water":"ocean",
        "underwater":"ocean",
        "ruin":"ruins",
        "ice":"arctic",
        "marshes":"swamp",
        "forests":"forest",
        "underground":"caves",
        "aquatic":"ocean",
        "cave":"caves",

    }

    try:
        eobj = Environment.objects.get(key=env_name)
        return eobj
    except:
        pass

    try:
        if env_name in synonyms.keys():
            eobj = Environment.objects.get(key=synonyms[env_name])
            return eobj
    except:
        pass

    try:
        eobj = Environment.objects.get(key=doc_key + "_" + env_name)
        return eobj
    except: 
        pass

    return None

if __name__ == '__main__':
    main()