"""Set damage_type and extra_damage_type on CreatureActionAttack fixtures from
the parent action's text.

The v1 to v2 conversion had an inverted check, so it never set damage_type and
put the last damage type in the text into extra_damage_type instead (#539).

Each attack already has its damage dice, so the primary type is taken from the
first damage clause in the text with matching dice. An attack stored without
dice takes the first damage clause, if it is the action's only attack. The
extra type is taken from the clause matching the stored extra dice, or else
from the clause joined to the primary one by "plus" ("... plus 3 (1d6) fire
damage"), since many attacks were stored without their extra dice. A type is
null when the text does not name a single type ("bludgeoning, piercing, or
slashing damage", "damage of the type determined by..."). Existing values are
not kept, since they all came from the faulty conversions.

Re-runnable, and works on the JSON files directly, so no database is needed:
    uv run python scripts/data_manipulation/fix_creature_attack_damage_types.py
    uv run python scripts/data_manipulation/fix_creature_attack_damage_types.py --check
"""
import argparse
import glob
import json
import os
import re
import sys
from collections import Counter

DATA_DIR = 'data/v2'
CORE_DAMAGE_TYPES = os.path.join(DATA_DIR, 'open5e', 'core', 'DamageType.json')


def load_damage_types():
    with open(CORE_DAMAGE_TYPES, encoding='utf-8') as f:
        return [o['pk'] for o in json.load(f)]


def build_clause_patterns(damage_types):
    types = '|'.join(damage_types)
    # "12 (2d6 + 5) piercing damage", also "magical piercing damage", and
    # "piercing plus ..." or "piercing and 3 (1d6) fire damage".
    dice = re.compile(
        r'\((\d+)\s*d\s*(\d+)(?:\s*[+\-−–]\s*\d+)?\)\s*(?:(?:magical|ongoing)\s+)?'
        r'(' + types + r')\s+(?:damage\b|plus\b|and\s+\d)',
        re.IGNORECASE)
    # "1 piercing damage", for attacks with no dice.
    flat = re.compile(
        r'(?<![\d(])(\d+)\s+(' + types + r')\s+damage\b', re.IGNORECASE)
    return dice, flat


def damage_clauses(desc, patterns):
    """Return the damage clauses in desc, in order, as (start, end, dice, type)."""
    dice, flat = patterns
    clauses = [(m.start(), m.end(3), (int(m.group(1)), 'D' + m.group(2)), m.group(3).lower())
               for m in dice.finditer(desc)]
    clauses += [(m.start(), m.end(2), int(m.group(1)), m.group(2).lower())
                for m in flat.finditer(desc)]
    return sorted(clauses)


def find_clause(clauses, die_count, die_type, bonus, after=-1):
    """The first clause starting after `after` whose dice match, or None."""
    if die_count and die_type:
        wanted = (die_count, die_type)
    elif die_count:
        # Flat damage such as "1 piercing damage" was stored as a die count.
        wanted = die_count
    elif bonus:
        wanted = bonus
    else:
        return None
    return next((c for c in clauses if c[0] > after and c[2] == wanted), None)


def plus_clause(desc, clauses, primary):
    """The extra damage clause joined to the primary one, as in "... plus 3 (1d6) fire damage".

    It must be in the same sentence, introduced by "plus" or "and", so damage
    from a failed save ("taking 10 (3d6) poison damage") is not counted.
    """
    for clause in clauses:
        if clause[0] <= primary[0]:
            continue
        between = desc[primary[1]:clause[0]]
        if re.search(r'\.\s', between):
            return None
        # Dice clauses start at the "(", after the average; flat ones at the number.
        if re.search(r'\b(?:plus|and)\s+(?:\d+\s*)?$', between):
            return clause
    return None


def fix_attack(fields, desc, patterns, sole_attack):
    """Return (damage_type, extra_damage_type, unresolved) for one attack."""
    clauses = damage_clauses(desc, patterns)
    unresolved = []

    has_damage = fields['damage_die_count'] or fields['damage_bonus']
    if has_damage:
        primary = find_clause(
            clauses, fields['damage_die_count'], fields['damage_die_type'], fields['damage_bonus'])
        if primary is None:
            unresolved.append('damage_type')
    elif sole_attack and clauses:
        # Some attacks were stored without their dice. If the action has no
        # other attacks, its first damage clause is this attack's damage.
        primary = clauses[0]
    else:
        primary = None
    damage_type = primary[3] if primary else None

    # Prefer the clause matching the stored extra dice. Many attacks were
    # stored without extra dice, or with the wrong ones, so otherwise use the
    # clause joined to the primary damage by "plus".
    extra = None
    has_extra = fields['extra_damage_die_count'] or fields['extra_damage_bonus']
    if has_extra:
        extra = find_clause(
            clauses, fields['extra_damage_die_count'], fields['extra_damage_die_type'],
            fields['extra_damage_bonus'], after=primary[0] if primary else -1)
    if extra is None and primary:
        extra = plus_clause(desc, clauses, primary)
    if extra is None and has_extra:
        unresolved.append('extra_damage_type')
    extra_damage_type = extra[3] if extra else None

    return damage_type, extra_damage_type, unresolved


def read_fixture(path):
    """Load a fixture and work out how to write it back without reformatting it."""
    with open(path, encoding='utf-8') as f:
        raw = f.read()
    objects = json.loads(raw)
    for style in (standard_style, django_style):
        text = style(objects)
        if raw in (text, text + '\n'):
            return objects, style, raw.endswith('\n')
    raise ValueError(f'{path} is not in a recognised fixture format.')


def standard_style(objects):
    return json.dumps(objects, indent=2, sort_keys=True, ensure_ascii=False)


def django_style(objects):
    return '[\n' + ',\n'.join(
        json.dumps(o, indent=2, sort_keys=True, ensure_ascii=False) for o in objects) + '\n]'


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('--check', action='store_true',
                        help='Report changes without writing them; exit 1 if any are needed.')
    parser.add_argument('--verbose', action='store_true',
                        help='List every attack whose type could not be read from its text.')
    args = parser.parse_args()

    patterns = build_clause_patterns(load_damage_types())
    total_changed = 0

    for attack_path in sorted(glob.glob(f'{DATA_DIR}/**/CreatureActionAttack.json', recursive=True)):
        action_path = os.path.join(os.path.dirname(attack_path), 'CreatureAction.json')
        with open(action_path, encoding='utf-8') as f:
            descs = {o['pk']: o['fields']['desc'] for o in json.load(f)}
        attacks, style, trailing_newline = read_fixture(attack_path)
        attacks_per_action = Counter(a['fields']['parent'] for a in attacks)

        changed = 0
        unresolved = []
        for attack in attacks:
            fields = attack['fields']
            damage_type, extra_damage_type, missing = fix_attack(
                fields, descs[fields['parent']], patterns,
                sole_attack=attacks_per_action[fields['parent']] == 1)
            if missing:
                unresolved.append((attack['pk'], missing))
            if (fields['damage_type'], fields['extra_damage_type']) != (damage_type, extra_damage_type):
                fields['damage_type'] = damage_type
                fields['extra_damage_type'] = extra_damage_type
                changed += 1

        print(f'{attack_path}: {changed} of {len(attacks)} attacks changed, '
              f'{len(unresolved)} not readable from text')
        if args.verbose:
            for pk, missing in unresolved:
                print(f'    {pk}: {", ".join(missing)}')

        if changed and not args.check:
            with open(attack_path, 'w', encoding='utf-8') as f:
                f.write(style(attacks) + ('\n' if trailing_newline else ''))
        total_changed += changed

    if args.check and total_changed:
        sys.exit(1)


if __name__ == '__main__':
    main()
