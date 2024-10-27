from django.template.defaultfilters import slugify

import json
import csv

from api_v2.models import Creature
from api_v2.models import Environment

def main():
    file = "./scripts/data_manipulation/monsters - 5.1 SRD.csv"
    doc_key = "srd"
    unfound=0


    with open(file, 'r', encoding='utf-8') as csvf:
        monsters = csv.DictReader(csvf)

        for monster in monsters:
            for n in range(0,20):
                ename = "environments/{}".format(n)
                if monster[ename] is not None and monster[ename] is not "":
                    #print(monster['name'],monster[ename])
                    creature_key = "{}_{}".format(doc_key,slugify(monster['name']))
                    env = slugify(monster[ename])
                    #print("{} {}".format(creature_key, env))
                    cobj = Creature.objects.get(key=creature_key)
                    e = get_env(env, doc_key=doc_key)
                    if e is None:
                        unfound+=1
                        print("Couldn't find {}".format(env))

    print("{} unfound environemnts.".format(unfound))

def get_env(env_name, doc_key):
    synonyms={
        "coastal":"coast",
        "hill":"hills",
        "mountains":"mountain",
        "plains":"grassland",
        "caverns":"caves",
        "underdark":"underworld",
        "volcano":"mountain",
        "settlement":"urban",
        "jungle":"forest",
        "tundra":"arctic",
        "water":"ocean",
        "underwater":"ocean",
        "ruin":"ruins",
        "ice":"arctic"
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