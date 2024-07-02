from django.apps import apps
from django.template.defaultfilters import slugify

from api_v2 import models as v2

def key_rewrite():
    for pub in v2.Publisher.objects.order_by('key'):
        pubq = v2.Publisher.objects.filter(key=pub.key).order_by('pk')

        # Create a Document fixture for each document.
        for doc in v2.Document.objects.filter(publisher=pub):
            docq = v2.Document.objects.filter(key=doc.key).order_by('pk')

            for model in apps.get_models():
                SKIPPED_MODEL_NAMES = ['Document', 'Ruleset', 'License', 'Publisher','SearchResult']
                CHILD_MODEL_NAMES = ['Trait', 'Capability', 'Benefit', 'FeatureItem', 'CastingOption']

                if model._meta.app_label == 'api_v2' and model.__name__ not in SKIPPED_MODEL_NAMES:
                    if model.__name__ in CHILD_MODEL_NAMES:
                        if model.__name__ == 'Trait':
                            modelq = model.objects.filter(race__document=doc).order_by('pk')
                        if model.__name__ == 'Capability':
                            modelq = model.objects.filter(feat__document=doc).order_by('pk')
                        if model.__name__ == 'Benefit':
                            modelq = model.objects.filter(background__document=doc).order_by('pk')
                        if model.__name__ == 'CastingOption':
                            modelq = model.objects.filter(spell__document=doc).order_by('pk')
                        if model.__name__ == 'FeatureItem':
                            modelq = model.objects.filter(feature__document=doc).order_by('pk')
                    else:
                        modelq = model.objects.filter(document=doc).order_by('pk')


                        for mo in modelq.all():
                            newpk = slugify(mo.name + "-" + doc.key)

                            if model.__name__ == "CreatureAttack":
                                newpk = slugify(mo.creature_action.creature.name + "-" + doc.key  +"-"+ mo.name)

                            if model.__name__ == "CreatureAction":
                                newpk = slugify(mo.creature.name + "-" + doc.key  +"-"+ mo.name)

                            if model.__name__ == "DamageType":
                                newpk = slugify(mo.name)

                            if newpk != mo.key:
                                print("MODEL:{}    PK:{}    NEWPK:   {}".format(model.__name__,mo.key,newpk))
