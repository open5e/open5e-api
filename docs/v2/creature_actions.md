Creature actions
================

These are the fields that appear in the JSON as returned by the server.


Fields for creature actions
---------------------------

- `name`

  **Example values:** `"Longsword"`, `"Multiattack"`, `"Frightful Presence"`

  The name of the creature action.

- `desc`

  **Example values:** `"Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 4 (1d4 + 2) piercing
  damage.\n"`, `"The hippogriff makes two attacks: one with its beak and one with its claws.\n"`

  The human-readable description of the action, pulled directly from the SRD.

- `uses_per_day` (optional)

  **Example values:** `1`, `3`, `4`

  If the action is limited by uses per day, this is how many uses are allowed.

- `recharge_on_roll` (optional)

  **Example values:** `4`, `5`, `6`

  If the action recharges on a die roll, this is the number that must be rolled.

- `recharge_after_rest` (optional)

  **Value:** `true`

  If the action recharges after a short or long rest then this is set.

- `attacks` (optional)

  **Value:** Array of action objects (see below)

  If this action is an attack, the entries in this array define each possible attack variation.


Fields for creature attack actions
----------------------------------

- `name`

  **Example values:** `"Claw attack"`, `"Longsword attack (if used with two hands)"`

  The name of the attack.

- `attack_type`

  **Allowed values:** `"SPELL"`, `"WEAPON"`

  Whether this is a Weapon or Spell attack.

- `to_hit_mod`

  **Example values:** `9`, `10`, `7`

  The attack roll modifier.

- `reach_ft` (melee attacks only)

  **Example values:** `5`, `10`, `15`

  Reach for melee attacks, in feet.

- `range_ft` (ranged attacks only)

  **Example values:** `60`, `150`, `20`

  Normal range for ranged attacks, in feet.

- `long_range_ft` (ranged attacks only; optional)

  **Example values:** `120`, `320`, `400`

  Long range for ranged attacks, in feet.

- `target_creature_only`

  **Allowed values:** `true`, `false`

  If an attack can target creatures only and not objects.

- `damage` (optional)

  The damage the attack deals, if any.

  - `amount`

    **Example values**: `12`, `17`, `5`

    The fixed amount of damage the attack may deal. Some attacks deal only 1 damage, in which case
    the die count/type and bonus fields are absent.

  - `die_count` (optional)

    **Example values**: `1`, `4`, `0`

    The number of dice to roll for damage.

  - `die_type` (optional)

    **Allowed values**: `D4`, `D6`, `D8`, `D10`, `D12`, `D20`

    What kind of die to roll for damage.

  - `bonus` (optional)

    **Example values**: `4`, `2`, `0`

    The damage roll modifier.

  - `type`

    **Allowed values**: `"ACID"`, `"BLUDGEONING"`, `"COLD"`, `"FIRE"`, `"FORCE"`, `"LIGHTNING"`,
      `"NECROTIC"`, `"PIERCING"`, `"POISON"`, `"PSYCHIC"`, `"RADIANT"`, `"SLASHING"`, `"THUNDER"`

    What kind of damage this attack deals.

- `extra_damage` (optional)

  Will be present if the attack deals secondary damage in addition to its main damage. Same fields
  as "damage" above.
