import hashlib
import os
# This file is used to serve data to the /version endpoint of the API.
# For production (and staging) deploys, this file is overwritten at build time.

def GetHashofDirs(directory):
    """
    Hash directories for 
    Adapted from: https://stackoverflow.com/questions/24937495/how-can-i-calculate-a-hash-for-a-filesystem-directory-using-python
    """

    digest = hashlib.sha256()
    if not os.path.exists(directory):
        raise IOError

    for root, _, files in os.walk(directory):
      for names in files:
        filepath = os.path.join(root,names)
        with open(filepath, 'rb') as file:
           digest = hashlib.file_digest(file, "sha256")
                

    return digest.hexdigest()

DATA_V1_HASH = GetHashofDirs("./data/v1")
DATA_V2_HASH = GetHashofDirs("./data/v2")
API_V1_HASH = GetHashofDirs("./api")
API_V2_HASH = GetHashofDirs("./api_v2")
