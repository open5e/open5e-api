from django.template.defaultfilters import slugify

import json

from api_v2 import models as v2_models

import glob


def get_images():
    input_dir = './data/images/'
    print("getting images in {}".format(input_dir))

    rel_image_paths = glob.glob(input_dir+'**/*.svg', recursive=True)

    for rep in rel_image_paths:
        print(rep)
