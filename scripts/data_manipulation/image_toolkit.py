from django.template.defaultfilters import slugify

import json

from api_v2 import models as v2_models

import glob


def get_images():
    input_dir = './data/images/'
    print("getting images in {}".format(input_dir))

    rel_image_paths = glob.glob(input_dir+'**/*.svg', recursive=True)
    rei_count=0

    for rep in rel_image_paths:
        rei_count+=1
    print("Found {} image files in {}".format(rei_count,input_dir))
        

    img_count=0
    for img in v2_models.Image.objects.all():
        img_count+=1
    
    print("Found {} Image objects in the database".format(img_count))