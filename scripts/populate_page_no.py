#!/usr/bin/env python3

"""Use a CSV of (monster name, page #) to populate page_no in monsters.json."""

import argparse
import csv
import json
import pathlib
import sys
from typing import Dict, List, Tuple


monster_to_page_no: Dict[str, int] = {}


def main():
    src_path, dest_path = parse_args()

    # Parse input
    monster_to_page_no = get_monster_to_page_no(src_path)
    with open(dest_path) as dest_file:
        monsters_json = json.load(dest_file)

    # Process JSON dict in memory
    for (name, page_no) in monster_to_page_no.items():
        monster = find_monster_by_name(monsters_json, name)
        monster['page_no'] = page_no

    # Write output
    with open(dest_path, 'w') as dest_file:
        json.dump(monsters_json, dest_file, indent=4)


def parse_args() -> Tuple[pathlib.Path, pathlib.Path]:
    """Determine the source CSV and dest JSON from the CLI args."""
    parser = argparse.ArgumentParser()
    parser.add_argument('src', type=pathlib.Path)
    parser.add_argument('dest', type=pathlib.Path)
    opts = parser.parse_args(sys.argv[1:])
    assert opts.src.exists(), f'Source file "{opts.src}" not found.'
    assert opts.dest.exists(), f'Destination file "{opts.dest}" not found.'
    return opts.src, opts.dest


def get_monster_to_page_no(source_csv_path: pathlib.Path) -> Dict[str, int]:
    """From the source file, return a dict of {monster name: page #}."""
    with open(source_csv_path) as csvfile:
        reader = csv.DictReader(csvfile)
        for line in reader:
            name = line['name']
            page_no = int(line['page_number'])
            assert name not in monster_to_page_no, \
                    f'Found duplicate monster "{name}"'
            monster_to_page_no[name] = page_no
    return monster_to_page_no


def find_monster_by_name(monsters_json: List[Dict[str, str]], name: str) -> Dict[str, str]:
    """Find and return the monster JSON object with the given name."""
    for monster in monsters_json:
        if monster['name'] == name:
            return monster
    raise ValueError(f'Monster named "{name}" not found')


if __name__ == '__main__':
    main()
