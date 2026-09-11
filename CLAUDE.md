# CLAUDE.md

> **Project-wide working rules and cross-repo context live in the FCM umbrella repo's `CLAUDE.md`**,
> loaded automatically when you work from the umbrella root. If you opened this repo directly instead
> of via the umbrella, relaunch from the umbrella root for the full context. This file holds only this
> repo's specific instructions.

Instructions for Claude (and other LLM agents) working in this repository.

## What this project is

`evennia-equipment` gives [Evennia](https://www.evennia.com/) characters equipment slots — what is
worn and what is wielded — and the carrying model that sits under them: what a character holds, what
it weighs, and how much it can take. Tagline: **"Wearslots and carrying capacity for Evennia."**

It was extracted from FullCircleMUD, and is now the mechanism in its own right — FCM is a consumer of
it rather than its source.

For the big-picture overview, read [README.md](README.md).
For the design wiki, read [docs/INDEX.md](docs/INDEX.md).

## Project status

**Core and contrib are both complete.** Five mixins, wearing and removing by name or by slot, four
hooks around them, equipment recovery across a world rebuild, and two required settings — plus four
optional commands in `contrib/`, merged as one cmdset and meant to be read and replaced.

Not adopted by any game yet. See [docs/progress.md](docs/progress.md).

## Where to read first

1. [docs/test-plan.md](docs/test-plan.md) — the cases the library commits to. **A behavioural change
   starts here**, not in the code. **Start here.**
2. [docs/design.md](docs/design.md) — the mixin family and the reasoning behind it.
3. [README.md](README.md) — what the library is and its status.
4. [docs/contrib.md](docs/contrib.md) — the optional commands, what each does, and what is not there.
5. [docs/INDEX.md](docs/INDEX.md) — map of all design docs.
6. [docs/interoperability.md](docs/interoperability.md) — this library against its siblings.

**FCM's `design/inventory-equipment.md` describes the system being extracted, not this library.** It
is the source to read for how the mechanism behaves today. It is not a specification for what belongs
here — it describes NFT ownership, gold and resource balances, durability decay, mob item spawning and
an item hierarchy tied to FCM's economy, and much of that stays in FCM.

## Load-bearing architectural principles

Every implementation decision must respect them.

1. **The library does not own game concepts.** Items, materials, currencies, rooms, stats, what an
   item does when worn and what any of it is worth belong to the consumer game. The library provides
   the slots, the carried set, and the weight and capacity arithmetic over them.

2. **No FCM-specific assumptions.** This library is being extracted from work on FullCircleMUD. NFTs,
   wallet addresses, gold, resources, FCM item and typeclass names, FCM's wearslot vocabulary — all
   stay in FCM. Default to "consumer concern" when uncertain.

3. **Test-first.** A case lands in [docs/test-plan.md](docs/test-plan.md), then the test, then the
   code. See [test-first-process.md](../../design/test-first-process.md) for the process and the
   rationale.

4. **Carrying is the base; wearing is a specialisation of it.** A game can have carrying without
   wearing, never the reverse. `EquipmentWearableMixin` extends `EquipmentCarriableMixin`, and
   `EquipmentWearslotsMixin` extends `EquipmentCarryingMixin`, on purpose — do not split the pairs
   apart on the grounds that the two mechanisms are independent. See
   [docs/design.md](docs/design.md) § The mixin family.

5. **Game concepts reach the library through the object, never through an import.** The library asks
   an item what it is; it never asks whether a sibling library is installed. A hook earns its place
   only if the library works without it being overridden.

6. **A name is resolved against what the wearer holds, and nothing wider.** `wear()` and `remove()`
   each take a string or an object, and match a string with `f_key_matches` — otherwise every command
   filters to find an object and then hands it to a method that filters again. Rooms, containers and
   other characters stay the command's problem. See [docs/design.md](docs/design.md) § Commands.

7. **Every walk over `contents` goes through `evennia-targeting`.** No inline comprehension over
   `contents` anywhere. The filters this library needs are published in
   [targeting.py](src/evennia_equipment/targeting.py), so a filter is defined once and fixed once
   rather than hand-rolled again in the next repo that needs it. See
   [docs/design.md](docs/design.md) § Filtering goes through evennia-targeting.

8. **Identity, never equality.** A consumer's typeclass may define `__eq__` and `__hash__` — by key,
   by token id — so "is this the object in that slot" is asked with `is`, and sets are keyed on
   `id()`. See [docs/design.md](docs/design.md) § Identity, never equality.

## Out of scope

Decided as questions arise — the library is too young for a settled list. Rulings so far:

- **The library owns no tables.** What is worn and what is carried is state on a character, which
  belongs to the consumer's game database. No alias, no router, no migration for a consumer to
  configure. Revisit only if the library gains data of its own that must outlive a rebuild or be read
  from more than one instance.

## Working conventions

- **Behavioural change starts in the test plan.** Add the case, write the test, then implement. Fill
  the **Test function** column when the test exists — it is a coverage claim and the linter checks it
  both ways.
- **Assign through the `AttributeProperty`, never `.db`.** `item.weight = 2.0` passes through
  `at_set()` and is validated; `item.db.weight = 2.0` writes straight past the descriptor and is not.
  The library reads and writes its own attributes through the property everywhere, so validation has
  one path rather than two. Evennia documents the bypass, and it is not fixable from the library
  side — so a consumer using `.db` gets whatever they set, and the docs say so.
- **Editing design docs.** Update or add design documents whenever an architectural decision is made
  or refined. Capture the *why*, not just the *what*. Index new docs in [docs/INDEX.md](docs/INDEX.md).
- **Don't put implementation detail in this file or README.** Link out to `docs/` instead. Keep
  `CLAUDE.md` and `README.md` stable; let `docs/` churn.
- **License.** BSD 3-Clause. Source files carry an SPDX header on the first line
  (`# SPDX-License-Identifier: BSD-3-Clause`).

## Documentation discipline (load-bearing)

Design documents in `docs/` must reflect decisions **actually discussed and agreed on with the project
owner**. They are not a place to forward-design the system from first principles or extrapolate
"reasonable defaults" from a starting point.

**Rules:**

1. **Only capture what was discussed and agreed.** If the conversation establishes a principle, do not
   extrapolate it into specifics that were not raised — slot names, weight units, API shapes, setting
   names.
2. **Flag open questions explicitly.** Write `[TBD — needs discussion: <what is open>]` so a future
   session picks the topic up deliberately rather than inheriting an unagreed assumption.
3. **Smaller is better.** Three discussed points captured faithfully beat three discussed points plus
   seven invented ones. Resist filling out sections "for completeness".

**The tempting source of unasked-for answers is FCM's own implementation.** It has a working shape for
every question this library will face, ready to be lifted. A shape lifted from it is an invention
unless it has been discussed here — the extraction is a design exercise, not a copy.

## Repository layout

```
evennia-equipment/
├── CLAUDE.md                  # this file
├── README.md
├── LICENSE                    # BSD 3-Clause
├── pyproject.toml
├── runtests.py                # standalone test runner; no gamedir required
├── .gitignore
├── docs/                      # design wiki (humans + LLMs)
│   ├── INDEX.md
│   ├── design.md              # the mixin family, and why
│   ├── installing.md          # what a consumer does, in order
│   ├── contrib.md             # the optional commands, and installing them
│   ├── progress.md
│   ├── test-plan.md
│   ├── interoperability.md
│   └── archive/               # historical context, not authoritative
├── src/
│   └── evennia_equipment/     # library code (src layout)
│       ├── __init__.py
│       ├── apps.py            # AppConfig — ready() runs the boot check
│       ├── carriable.py       # EquipmentCarriableMixin — an item's weight
│       ├── carrying.py        # EquipmentCarryingMixin — the total, and capacity
│       ├── config.py          # the setting, check_settings(), the accessors
│       ├── container.py       # EquipmentContainerMixin — carried and carrying
│       ├── wearable.py        # EquipmentWearableMixin — an item's slot groups
│       ├── wearslots.py       # EquipmentWearslotsMixin — slots, wear, remove
│       ├── targeting.py       # the filters this library publishes for evennia-targeting
│       ├── log.py             # binds equipment_log via evennia-logging-extension → equipment.log
│       ├── tests.py           # unit tests, run via runtests.py
│       └── contrib/           # optional; core is complete without it
│           ├── __init__.py    # the surface — the four commands and the cmdset
│           ├── commands.py    # wear, remove, equipment, inventory
│           ├── cmdset.py      # EquipmentCmdSet
│           └── utils.py       # normalising and matching a typed slot name
└── tests/                     # standalone test infrastructure
    ├── __init__.py
    ├── game_typeclasses.py    # real typeclasses carrying the mixins
    ├── slot_enums.py          # slot enums; imports nothing but enum
    ├── test_settings.py
    └── urls.py
```

No `examples/` — a demo gamedir would only repeat what `contrib/` already shows, and the `CW`–`CS`
cases exercise the commands against real Evennia objects.

## Tools and environment

- Python 3.10+ (pinned via `pyproject.toml`).
- Runtime dependencies: Evennia, `evennia-logging-extension` and `evennia-targeting`. None is
  published, so a dev venv installs the siblings from their checkouts:
  `pip install -e ../evennia-logging-extension -e ../evennia-targeting`.
- **Tests use Django's test runner** via `python runtests.py`, which bootstraps Django then calls
  `evennia._init()`, as the siblings do. Not pytest, and no gamedir required.
- Development uses a dedicated venv at `venv/` (gitignored), independent of any consumer game.

## Sibling libraries to reference

- **[../evennia-survival/](../evennia-survival/)** — the closest analogue: the same extraction from
  FCM, and the one that has already drawn its mechanism/content line. Its
  [docs/design.md](../evennia-survival/docs/design.md) § *Out of scope* is worth reading for how that
  line was argued, not for what it decided.
- **[../evennia-targeting/](../evennia-targeting/)** — a hard dependency, not just a reference. Read
  its [docs/architecture.md](../evennia-targeting/docs/architecture.md) § *Where an extension goes*
  before adding a filter here, and its [docs/testing.md](../evennia-targeting/docs/testing.md) for the
  validators every published filter is tested against.
- **[../evennia-scaling/](../evennia-scaling/)** and **[../evennia-archive/](../evennia-archive/)** —
  the reference shape for repo structure, the test runner and the docs surfaces.
