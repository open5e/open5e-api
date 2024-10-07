# The purpose of this file is to:
# Go through the fixtures in the /data directory
# Review the values in them for proper encoding and any weird characters.
# Fail if it finds any, and error with a good message to find it.

import argparse
import requests
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-d', '--dir', required=True, type=Path,
        help='Directory to recursively check files for validation.')

    args = parser.parse_args()
    print("For a given input directory, this goes and checks each .json")
    print("file in all subdirectories for valid/invalid characters.")

    error = False

    for path in Path(args.dir).rglob('*.json'):
        with open(path,'r',encoding='utf-8') as f:
            lines = f.readlines()
            line_no = 1
            for line in lines:

                if "\\u" in line:
                    error = True
                    char = "\\u{}".format(line.split("\\u")[1][0:4])
                    # This should detect if any explicit unicode
                    # characters are being specified as part of 
                    # descriptions.
                    print("UNICODE ESCAPE CHARS FOUND: {}:{}   {}".format(path, line_no, char))
                line_no+=1

    if error:
        exit("Found Unicode Characters")

if __name__ == '__main__':
    main()