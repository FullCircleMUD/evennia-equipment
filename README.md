# evennia-equipment

Equipment slots for Evennia characters — what is worn and what is wielded — and the carrying model
underneath: what a character holds, what it weighs, and how much it can take.

## Status

**Early — the weight half works, the wearing half is not written.** An object declares a weight, a
carrier totals what it holds and answers what more it can take, and the total keeps itself current
through arrivals, departures, reloads and weight changes in place. Containers nest and their contents
count through them. Equipment slots are still to come. Nothing is published. See
[docs/progress.md](https://github.com/FullCircleMUD/evennia-equipment/blob/main/docs/progress.md).

## The problem it solves

Every MUD writes this twice: a set of slots an item can occupy, a rule about which items fit which
slot, and a weight budget that decides what a character can pick up. The mechanism is the same each
time; only the slot names, the units and the items are the game's.

It is also a system with a known trap in it. Worn items are still held, so "my inventory" and "what
this object contains" are two different sets that look identical from the outside — and code that
conflates them is wrong in ways that surface much later, in a capacity total or a listing that offers
a player the armour they are already wearing.

## The approach

The library supplies the mechanism: the slots, the carried set and the distinction between the two, and
the weight and capacity arithmetic over them. The game supplies the content — what an item is, what
it is made of, what wearing it does, and what happens to a character who is carrying too much.

`[TBD — needs discussion: exactly where that line falls. Drawing it is the first task of the
extraction, not something settled here.]`

## Is this for you?

Probably, if you want worn and wielded equipment in an Evennia game and would rather configure slots
than write them.

Probably not, if your game has no equipment slots and no weight limit, or if your items are not
Evennia objects.

## Install

Nothing is published yet. Editable install for development against a checkout:

```
git clone https://github.com/FullCircleMUD/evennia-equipment.git
cd evennia-equipment
python -m venv venv
# Activate the venv (platform-specific)
pip install evennia
pip install -e .
python runtests.py
```

## Learn more

- [docs/INDEX.md](https://github.com/FullCircleMUD/evennia-equipment/blob/main/docs/INDEX.md) — the design wiki
- [docs/design.md](https://github.com/FullCircleMUD/evennia-equipment/blob/main/docs/design.md) — the mixin family and the reasoning behind it
- [docs/test-plan.md](https://github.com/FullCircleMUD/evennia-equipment/blob/main/docs/test-plan.md) — every case the library commits to covering
- [docs/interoperability.md](https://github.com/FullCircleMUD/evennia-equipment/blob/main/docs/interoperability.md) — this library against its siblings
- [CLAUDE.md](https://github.com/FullCircleMUD/evennia-equipment/blob/main/CLAUDE.md) — context for LLM agents working in this repo

## Licence

BSD 3-Clause. See [LICENSE](https://github.com/FullCircleMUD/evennia-equipment/blob/main/LICENSE).
