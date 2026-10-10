"""Store "Melee or Ranged" creature attacks as a separate melee attack and
ranged attack (#1005).

Actions like "Javelin. Melee or Ranged Weapon Attack: +4 to hit, reach 5 ft.
or range 30/120 ft." were stored as one attack with both reach and range in
most books, and as two attacks in srd-2014. Each attack now has either a reach
(melee) or a range (ranged):

- An action with a single attack that has both is split. The existing attack
  keeps its key and becomes the melee attack ("Javelin Melee attack"), and a
  ranged copy is added with "-ranged" in its key ("Javelin Ranged attack").
- If the text gives the ranged damage separately ("7 (1d6 + 4) piercing damage
  at range", "3 (1d6) piercing damage if thrown"), the ranged attack gets those
  dice. The types are then set by fix_creature_attack_damage_types.py.
- A melee attack with the same range as a ranged attack in its action has
  that range removed.

Attacks whose text gives only a reach or only a range are left alone.

Re-runnable, and works on the JSON files directly:
    uv run python scripts/data_manipulation/split_melee_or_ranged_attacks.py
    uv run python scripts/data_manipulation/fix_creature_attack_damage_dice.py
    uv run python scripts/data_manipulation/fix_creature_attack_damage_types.py
"""
import argparse
import copy
import glob
import json
import os
import re
import sys
from collections import defaultdict

from fix_creature_attack_damage_dice import build_clause_patterns, damage_clauses
from fix_creature_attack_damage_types import DATA_DIR, load_damage_types, read_fixture

# Not \b: bfrd wraps it in underscores ("_Melee or Ranged Weapon Attack:_").
MELEE_OR_RANGED = re.compile(r'(?<![A-Za-z])Melee or Ranged(?![A-Za-z])', re.IGNORECASE)
# Text after a damage clause marking it as the ranged damage.
RANGED_ONLY = re.compile(r'^[^.;]*?\b(?:at range|if thrown|when thrown)\b', re.IGNORECASE)


def ranged_clause(desc, clauses):
    """The damage clause the text gives for ranged attacks only, or None."""
    for i, clause in enumerate(clauses):
        end = clauses[i + 1]['start'] if i + 1 < len(clauses) else len(desc)
        if RANGED_ONLY.match(desc[clause['end']:end]):
            return clause
    return None


def split(attack, desc, patterns):
    """Turn a single melee-or-ranged attack into (melee, ranged)."""
    melee = attack
    ranged = copy.deepcopy(attack)
    name = attack['fields']['name']
    base = name[:-len(' attack')] if name.endswith(' attack') else name
    melee['fields'].update(name=f'{base} Melee attack', range=None, long_range=None)
    ranged['fields'].update(name=f'{base} Ranged attack', reach=None)
    ranged['pk'] = re.sub(r'-attack$', '', attack['pk']) + '-ranged-attack'

    clause = ranged_clause(desc, damage_clauses(desc, patterns))
    if clause:
        count = clause['count']
        ranged['fields'].update(
            damage_die_count=count, damage_die_type=clause['die'],
            damage_bonus=clause['bonus'] if count is None or clause['bonus'] else None)
        # If the stored damage was the ranged damage, the melee attack needs
        # the melee damage: the first clause that isn't the ranged one.
        stored = (melee['fields']['damage_die_count'], melee['fields']['damage_die_type'])
        if stored == (count, clause['die']):
            other = next((c for c in damage_clauses(desc, patterns) if c['start'] != clause['start']), None)
            if other:
                melee['fields'].update(damage_die_count=other['count'], damage_die_type=other['die'],
                                       damage_bonus=other['bonus'] if other['bonus'] else None)
    return melee, ranged


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('--check', action='store_true',
                        help='Report changes without writing them; exit 1 if any are needed.')
    args = parser.parse_args()

    patterns = build_clause_patterns(load_damage_types())
    total = 0
    for attack_path in sorted(glob.glob(f'{DATA_DIR}/**/CreatureActionAttack.json', recursive=True)):
        action_path = os.path.join(os.path.dirname(attack_path), 'CreatureAction.json')
        with open(action_path, encoding='utf-8') as f:
            descs = {o['pk']: o['fields']['desc'] for o in json.load(f)}
        attacks, style, trailing_newline = read_fixture(attack_path)
        was_sorted = [a['pk'] for a in attacks] == sorted(a['pk'] for a in attacks)

        by_action = defaultdict(list)
        for attack in attacks:
            by_action[attack['fields']['parent']].append(attack)

        added, cleared = [], 0
        for action, group in by_action.items():
            if not MELEE_OR_RANGED.search(descs[action]):
                continue
            if len(group) == 1 and group[0]['fields']['reach'] and group[0]['fields']['range']:
                _, ranged = split(group[0], descs[action], patterns)
                added.append((group[0], ranged))
                continue
            for melee in group:
                f = melee['fields']
                if f['reach'] and f['range'] and any(
                        r is not melee and not r['fields']['reach']
                        and (r['fields']['range'], r['fields']['long_range']) == (f['range'], f['long_range'])
                        for r in group):
                    f.update(range=None, long_range=None)
                    cleared += 1

        existing = {a['pk'] for a in attacks}
        for melee, ranged in added:
            if ranged['pk'] in existing:
                sys.exit(f'{ranged["pk"]} already exists in {attack_path}')
            attacks.insert(attacks.index(melee) + 1, ranged)
        if was_sorted:
            attacks.sort(key=lambda a: a['pk'])

        print(f'{attack_path}: {len(added)} attacks split, {cleared} melee ranges cleared')
        if (added or cleared) and not args.check:
            with open(attack_path, 'w', encoding='utf-8') as f:
                f.write(style(attacks) + ('\n' if trailing_newline else ''))
        total += len(added) + cleared

    if args.check and total:
        sys.exit(1)


if __name__ == '__main__':
    main()
