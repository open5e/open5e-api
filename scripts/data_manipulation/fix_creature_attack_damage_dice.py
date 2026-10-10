"""Set the damage dice and bonuses on CreatureActionAttack fixtures from the
parent action's text (#1004).

Many attacks are missing their damage bonus ("13 (2d8 + 4)" stored as 2d8 with
no bonus), their extra damage ("plus 7 (2d6) poison damage"), or all of their
damage, and a few have the wrong extra dice or bonus sign.

For each attack, the primary damage clause in the text is the first one whose
dice match the stored dice. An attack stored without damage takes the first
clause, if it is the action's only attack. The extra damage is the clause
joined to the primary one by "plus" or "and" in the same sentence. Flat damage
("1 piercing damage") is stored as a bonus with no dice. Stored damage that
matches nothing in the text is replaced with the first clause if the action
has only one attack, and otherwise left alone. Both are listed for review.

Run this before fix_creature_attack_damage_types.py, which picks each type
using the dice. Both are re-runnable and work on the JSON files directly:
    uv run python scripts/data_manipulation/fix_creature_attack_damage_dice.py
    uv run python scripts/data_manipulation/fix_creature_attack_damage_types.py
"""
import argparse
import glob
import json
import os
import re
import sys
from collections import Counter

from fix_creature_attack_damage_types import DATA_DIR, load_damage_types, read_fixture

DAMAGE_FIELDS = ('damage_die_count', 'damage_die_type', 'damage_bonus')
EXTRA_FIELDS = ('extra_damage_die_count', 'extra_damage_die_type', 'extra_damage_bonus')
# "plus 2 (1d4) Charisma damage" reduces an ability score; it is not hit point damage.
ABILITY_DAMAGE = re.compile(
    r'\s*(?:Strength|Dexterity|Constitution|Intelligence|Wisdom|Charisma)\b', re.IGNORECASE)


def build_clause_patterns(damage_types):
    types = '|'.join(damage_types)
    # Any dice in parentheses, "18 (3d6 + 8)", whatever type follows: the
    # amount is needed even when the text offers a choice of types.
    dice = re.compile(r'\((\d+)\s*d\s*(\d+)(?:\s*([+\-−–])\s*(\d+))?\)', re.IGNORECASE)
    flat = re.compile(r'(?<![\d(])(\d+)\s+(' + types + r')\s+damage\b', re.IGNORECASE)
    return dice, flat


def damage_clauses(desc, patterns):
    """Return the damage clauses in desc, in order, as dicts."""
    dice, flat = patterns
    clauses = []
    for m in dice.finditer(desc):
        if ABILITY_DAMAGE.match(desc, m.end()):
            continue
        bonus = int(m.group(4)) if m.group(4) else 0
        if m.group(3) and m.group(3) != '+':
            bonus = -bonus
        clauses.append({'start': m.start(), 'end': m.end(), 'count': int(m.group(1)),
                        'die': 'D' + m.group(2), 'bonus': bonus})
    for m in flat.finditer(desc):
        clauses.append({'start': m.start(), 'end': m.end(2), 'count': None, 'die': None,
                        'bonus': int(m.group(1))})
    return sorted(clauses, key=lambda c: c['start'])


def plus_clause(desc, clauses, primary):
    """The clause joined to `primary` by "plus" or "and" in the same sentence, or None."""
    for clause in clauses:
        if clause['start'] <= primary['start']:
            continue
        between = desc[primary['end']:clause['start']]
        if re.search(r'\.\s', between):
            return None
        if re.search(r'\b(?:plus|and)\s+(?:\d+\s*)?$', between):
            return clause
    return None


def find_primary(fields, desc, clauses, sole_attack):
    """Return (primary clause or None, note for review or None)."""
    count, die, bonus = (fields[f] for f in DAMAGE_FIELDS)
    if not clauses:
        # No damage in the text, e.g. "The chimera uses its Bite attack."
        return None, None
    primary = None
    if count and die:
        primary = next((c for c in clauses if (c['count'], c['die']) == (count, die)), None)
        if primary:
            # "1 piercing damage plus 14 (4d6) psychic damage" stored with 4d6
            # as the main damage: the real main damage is the clause before it.
            earlier = next((c for c in clauses if c['start'] < primary['start']
                            and plus_clause(desc, clauses, c) is primary), None)
            return earlier or primary, None
    elif count or bonus:
        # Flat damage, stored as a die count or as a bonus.
        primary = next((c for c in clauses if c['count'] is None and c['bonus'] == (count or bonus)), None)
        if primary:
            return primary, None
    stored = count or bonus
    if not sole_attack:
        return None, ('stored damage matches nothing in the text' if stored
                      else 'no damage stored, and the action has several attacks')
    # The action's only attack: its damage is the first in the text.
    return clauses[0], 'replaced stored damage that matched nothing in the text' if stored else None


def main_values(clause, current_bonus):
    if clause['count'] is None:
        return None, None, clause['bonus']
    # Keep the existing null or 0 for "(3d6)", which the data stores both ways.
    if clause['bonus'] == 0 and current_bonus in (None, 0):
        return clause['count'], clause['die'], current_bonus
    return clause['count'], clause['die'], clause['bonus']


def extra_values(clause):
    if clause['count'] is None:
        return None, None, clause['bonus']
    return clause['count'], clause['die'], clause['bonus']


def fix_attack(fields, desc, patterns, sole_attack):
    """Return (new damage values, new extra values, review reason or None)."""
    clauses = damage_clauses(desc, patterns)
    current = tuple(fields[f] for f in DAMAGE_FIELDS)
    current_extra = tuple(fields[f] for f in EXTRA_FIELDS)

    primary, note = find_primary(fields, desc, clauses, sole_attack)
    if primary is None:
        return current, current_extra, note

    damage = main_values(primary, fields['damage_bonus'])
    extra = plus_clause(desc, clauses, primary)
    # Keep the stored extra damage if the text has none joined by "plus".
    return damage, extra_values(extra) if extra else current_extra, note


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('--check', action='store_true',
                        help='Report changes without writing them; exit 1 if any are needed.')
    parser.add_argument('--verbose', action='store_true',
                        help='List every change, and every attack that needs review.')
    args = parser.parse_args()

    patterns = build_clause_patterns(load_damage_types())
    total_changed = 0
    review = []

    for attack_path in sorted(glob.glob(f'{DATA_DIR}/**/CreatureActionAttack.json', recursive=True)):
        action_path = os.path.join(os.path.dirname(attack_path), 'CreatureAction.json')
        with open(action_path, encoding='utf-8') as f:
            descs = {o['pk']: o['fields']['desc'] for o in json.load(f)}
        attacks, style, trailing_newline = read_fixture(attack_path)
        attacks_per_action = Counter(a['fields']['parent'] for a in attacks)

        changed = 0
        for attack in attacks:
            fields = attack['fields']
            damage, extra, note = fix_attack(
                fields, descs[fields['parent']], patterns,
                sole_attack=attacks_per_action[fields['parent']] == 1)
            if note:
                review.append((attack['pk'], note))
            new = dict(zip(DAMAGE_FIELDS + EXTRA_FIELDS, damage + extra))
            if any(fields[k] != v for k, v in new.items()):
                if args.verbose:
                    print(f"    {attack['pk']}: "
                          + ', '.join(f'{k} {fields[k]} -> {v}' for k, v in new.items() if fields[k] != v))
                fields.update(new)
                changed += 1

        print(f'{attack_path}: {changed} of {len(attacks)} attacks changed')
        if changed and not args.check:
            with open(attack_path, 'w', encoding='utf-8') as f:
                f.write(style(attacks) + ('\n' if trailing_newline else ''))
        total_changed += changed

    print(f'{len(review)} attacks to review:')
    for pk, note in review:
        print(f'    {pk}: {note}')

    if args.check and total_changed:
        sys.exit(1)


if __name__ == '__main__':
    main()
