# evennia-equipment

Equipment slots for Evennia characters — what is worn and what is wielded — and the carrying model
underneath: what a character holds, what it weighs, and how much it can take.

## Status

**Core works.** An object declares a weight and which slots it occupies; a wearer declares a body plan
and can wear, remove and list — by name or by slot, with hooks either side of both so a game can apply
whatever a worn item does. The carried total keeps itself current through arrivals, departures, reloads
and weight changes in place, containers nest, and a character's equipment survives a world rebuild.

Still to come: `contrib/`, four optional commands a player types. Nothing is published. See
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

You declare every slot your game has as one enum, and a small subclass per body plan naming which of
them each creature gets — humanoid, dog, horse.

An item's slots are a list of groups. Each group is one way of wearing the thing, and every slot in a
group is taken together — so a ring declares `[["LEFT_FINGER"], ["RIGHT_FINGER"]]` and fits either
hand, while a greatsword declares `[["WIELD", "HOLD"]]` and takes both. Two-handed weapons and
"a dog cannot wear a helmet" both fall out of that, with no rule of their own.

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
pip install -e ../evennia-targeting   # a dependency, and not published either
pip install -e .
python runtests.py
```

## Learn more

- [docs/installing.md](https://github.com/FullCircleMUD/evennia-equipment/blob/main/docs/installing.md) — everything a game does to get it running
- [docs/INDEX.md](https://github.com/FullCircleMUD/evennia-equipment/blob/main/docs/INDEX.md) — the design wiki
- [docs/design.md](https://github.com/FullCircleMUD/evennia-equipment/blob/main/docs/design.md) — the mixin family and the reasoning behind it
- [docs/test-plan.md](https://github.com/FullCircleMUD/evennia-equipment/blob/main/docs/test-plan.md) — every case the library commits to covering
- [docs/interoperability.md](https://github.com/FullCircleMUD/evennia-equipment/blob/main/docs/interoperability.md) — this library against its siblings
- [CLAUDE.md](https://github.com/FullCircleMUD/evennia-equipment/blob/main/CLAUDE.md) — context for LLM agents working in this repo

## Licence

BSD 3-Clause. See [LICENSE](https://github.com/FullCircleMUD/evennia-equipment/blob/main/LICENSE).
