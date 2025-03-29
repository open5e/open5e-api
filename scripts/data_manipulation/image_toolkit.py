from django.template.defaultfilters import slugify

import json

from api_v2 import models as v2_models

import glob


def main():
    extract_image_objects_from_dir('./data/images/','icon','elderberry',update=False)


def extract_image_objects_from_dir(directory, image_type, document_key, update=False):
    # Count image files in directory
    ifps=get_dir_images(directory=directory)

    # Count image objects associated to document
    i_objs = v2_models.Image.objects.filter(document=document_key)
    print("Found {} Image objects in the database".format(len(i_objs)))

    # For each image file in directory
    inserted_count=0
    for ifp in ifps:
        name = ifp.split('/')[-1].split('.')[0].capitalize()
        key = slugify(document_key+"_"+name)
        document = v2_models.Document.objects.get(key=document_key)

        if update:
            if v2_models.Image.objects.filter(pk=key).exists():
                print("Key collision when trying to insert {}".format(key))
                continue

            if v2_models.Image.objects.filter(file_path=ifp).exists():
                print("File path collision when trying to insert {}".format(ifp))
                continue
            
            v2_models.Image.objects.create(name=name,
                                    key=key,
                                    document=document,
                                    file_path=ifp,
                                    type='icon')
            inserted_count+=1

    print("Inserted {} images into the database.".format(inserted_count))


def get_dir_images(directory):
    dir_image_file_paths=[]
    print("Discovering image files in {}".format(directory))
    rel_image_paths = glob.glob(directory+'**/*.svg', recursive=True)
    rei_count=0

    for rep in rel_image_paths:
        dir_image_file_paths.append(rep)
    print("Found {} image files in {}".format(len(dir_image_file_paths),directory))
    return dir_image_file_paths


if __name__=="__main__":
    main()