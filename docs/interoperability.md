# Interoperability

This library against every `evennia-*` sibling library in `libraries/`. The `fcm-*` libraries are
deliberately absent: they are coupled to FullCircleMUD's game concepts and are not offered for outside
consumption, so a reader deciding what to co-install with this library cannot install them anyway.

Each section names the relationship — **hard dependency**, **optional integration**, or **no
coupling** — followed either by the constraints that apply or by an explicit clearance stating *why* it
is clear in terms of what this library does. "No known issues" is not a clearance.

**No library code exists yet**, so every statement below is provisional. A clearance given now rests on
the library having no behaviour to clear; re-confirm each one against the implementation as it lands
rather than inheriting it.

## evennia-ai-memory

`[TBD — needs discussion: not yet assessed.]`

## evennia-archive

`[TBD — needs discussion: not yet assessed. Worn equipment is a set of references from a character to
objects, and archive drops references rather than translating them — so what a restored character is
still wearing is a real question for both libraries.]`

## evennia-equipment

This library.

## evennia-llm-service

`[TBD — needs discussion: not yet assessed.]`

## evennia-message-bus

`[TBD — needs discussion: not yet assessed.]`

## evennia-mob-spawner

`[TBD — needs discussion: not yet assessed. Whether a spawned mob is equipped, and by whom, is a
consumer decision this library has not yet framed.]`

## evennia-portal-multiplex

**No coupling.** Neither library imports the other. Multiplex moves a player's session between
instances and touches sockets and protocols; this library holds state on a character object and issues
no session work.

## evennia-scaling

`[TBD — needs discussion: not yet assessed. A character that moves between instances carries what it
is wearing, so how equipment survives the move is real and unexamined.]`

## evennia-shards

`[TBD — needs discussion: not yet assessed. Shards scopes ORM access by `shard_id` and documents what
that does to off-thread work; whether anything here runs off the reactor thread is not yet decided.]`

## evennia-survival

`[TBD — needs discussion: not yet assessed. Carried weight and an upkeep meter are the obvious place
the two could meet — whether encumbrance feeds regeneration is a consumer rule, but neither library has
framed where it would be expressed.]`

## evennia-targeting

`[TBD — needs discussion: not yet assessed. Resolving "wear the boots" against a character's held
items is search, and the two libraries have overlapping opinions about which set is searched — see the
inventory-versus-contents decision in [test-plan.md](test-plan.md).]`

## evennia-world-builder

`[TBD — needs discussion: not yet assessed. Item prototypes are world content, so the question is
whether this library defines a capability that authored items declare, or stays out of it entirely.]`

## evennia-yaml-reader

**No coupling.** Neither library imports the other. yaml-reader depends only on `pyyaml`, has no
Evennia dependency and touches no database, so nothing it does is visible to this library and nothing
this library does is visible to it.
