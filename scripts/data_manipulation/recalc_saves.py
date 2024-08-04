
import json

from api_v2 import models as v2_models

from api.models import Monster as v1_model



def main():
    for monster in v1_model.objects.filter(document__slug='blackflag'):
        print(monster.slug)
        monster.strength_save = score_2_save(monster.strength_save)
        monster.dexterity_save = score_2_save(monster.dexterity_save)
        monster.constitution_save = score_2_save(monster.constitution_save)
        monster.wisdom_save = score_2_save(monster.wisdom_save)
        monster.charisma_save = score_2_save(monster.charisma_save)
        monster.intelligence_save = score_2_save(monster.intelligence_save)
        
        monster.save()

def score_2_save(score):
    savex2 = score - 10
    save = savex2 // 2
    return save


if __name__ == '__main__':
    main()