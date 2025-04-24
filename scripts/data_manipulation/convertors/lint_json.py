import glob
import json
import os
import sys

root_path = os.environ['OPEN_5E_ROOT']
sys.path.append(root_path)

folder_location = root_path + ('' if root_path.endswith('/') else '/') + 'data/'

filenames = glob.glob(folder_location + '**/*.json', recursive=True)

for filename in filenames:
    with open(filename, 'r') as f:
        file = f.read()

    js = json.loads(file)

    with open(filename, 'w') as f:
        f.write(json.dumps(js, indent=4, ensure_ascii=False))
