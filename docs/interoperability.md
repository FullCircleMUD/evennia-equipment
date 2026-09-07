# Interoperability

This library against every `evennia-*` sibling library in `libraries/`. The `fcm-*` libraries are
deliberately absent: they are coupled to FullCircleMUD's game concepts and are not offered for outside
consumption, so a reader deciding what to co-install with this library cannot install them anyway.

**What this library does, for a sibling deciding whether it matters.** It owns no tables, runs no
migrations and issues no ORM writes of its own — all of its state is Evennia attributes on objects the
consumer already has. It starts no scripts, dispatches nothing off the reactor thread, and does no
network work. It reads two settings, `EQUIPMENT_WEARSLOTS` and `EQUIPMENT_IDENTITY_ATTRIBUTE`, both
validated in `AppConfig.ready()`. It imports Evennia and `evennia-targeting`, and nothing else.

Each section names the relationship — **hard dependency**, **optional integration**, or **no
coupling** — followed either by the constraints that apply or by an explicit clearance stating *why* it
is clear in terms of what this library does. "No known issues" is not a clearance.

## evennia-ai-memory

**No coupling.** Neither library imports the other. ai-memory holds NPC memory and embeddings in its
own tables and calls out to an embedding service; this library owns no tables, makes no network calls
and writes only Evennia attributes on the objects it is mixed into.

## evennia-archive

**No coupling.** Neither library imports the other. **The two are complementary**, and this is the
pairing this library's recovery surface exists for.

An archive drops the character's items — it keeps references to nothing that will not survive a
rebuild. What comes back afterwards is restored to `contents` by whatever owns the items, and arrives
carrying nothing about what was worn. `update_worn_equipment_record()` and `restore_worn()` are the two
halves that close that: the record is written from live state before the archive, persisted on the
character, and read afterwards to put the same items back in the same slots.

The consumer wires the order — call the record before archiving, call the restore after the items are
back. The library cannot know when either moment is, and nothing it could hook would tell it without
learning that archiving exists. See [design.md](design.md) § *Recovering equipment after a rebuild*.

`EQUIPMENT_IDENTITY_ATTRIBUTE` is the join. A world rebuild reissues every primary key, so the record
is keyed on whatever the game already uses to identify an item permanently.

## evennia-equipment

This library.

## evennia-llm-service

**No coupling.** Neither library imports the other. llm-service makes API calls and manages threading
around them; this library dispatches nothing off the reactor thread and makes no network calls, so
there is nothing of its to block or be blocked by.

## evennia-message-bus

**No coupling.** Neither library imports the other. The bus carries messages between instances; this
library holds state on one object in one instance and publishes nothing.

## evennia-mob-spawner

**No coupling.** Neither library imports the other. The spawner creates mobs from spawn rules; whether
a spawned mob arrives equipped is the rule calling `wear()` on what it created, which needs no
knowledge on either side.

## evennia-portal-multiplex

**No coupling.** Neither library imports the other. Multiplex moves a player's session between
instances and touches sockets and protocols; this library holds state on a character object and issues
no session work.

## evennia-scaling

**No coupling.** Neither library imports the other. **The two are complementary**, and together with
archive and the game's own ownership records they are what makes a character transfer faithful rather
than approximate.

Scaling moves the character between instances; the archive on the way through costs it its equipment;
ownership records restore the items to `contents`; `restore_worn()` puts them back on. Each library is
useful on its own and none depends on another — the chain is assembled by the consumer, in that order.
See the archive section above for the equipment half of it.

The cost worth knowing: `restore_worn()` runs once per move, not once per session, and reports every
item as a failure if called twice. See `RW-03` in [test-plan.md](test-plan.md).

## evennia-shards

**No coupling.** Neither library imports the other. Shards scopes ORM access by `shard_id` and
constrains off-thread work; this library owns no models, writes no queries of its own, and dispatches
nothing off the reactor thread — its state is Evennia attributes on objects the consumer has already
loaded through whatever routing is in force.

## evennia-survival

**No coupling.** Neither library imports the other. Both hang state off a character, and they read
nothing of each other's. A game wanting encumbrance to slow regeneration reads `is_encumbered` in its
own survival hook; that is a consumer rule, and neither library needs to know the other is installed.

## evennia-targeting

**Hard dependency.** `carrying.py` and `wearslots.py` import `walk_contents`, `op_not` and
`f_excluding` unconditionally, and the package is declared in `pyproject.toml`. Installing this library
without targeting fails at import, not at first use.

Every walk this library makes over an object's `contents` goes through `walk_contents`. That is the
point of the dependency rather than a side effect of it: a filter defined once is fixed once, and a
second hand-rolled copy of "is this worn" in another repo is what the arrangement exists to prevent.

**This library publishes two filters**, in `src/evennia_equipment/targeting.py` per the module-name
convention targeting documents in its
[architecture.md](../../evennia-targeting/docs/architecture.md) § *Where an extension goes*:

| Filter | Matches |
|---|---|
| `f_worn_by(wearer)` | The items that wearer currently has on |
| `f_identity_in(identities)` | Items whose `wearslot_identity` is in a given set |

A consumer filtering by either uses these rather than writing their own. Both are factories, so the
data each closes over is read once per walk rather than once per object.

`f_identity_in` diverges from targeting's convention that a factory built with nothing raises
`ValueError`: an empty set matches nothing here, because an empty record is the ordinary state of a
wearer who had nothing on and `restore_worn()` reaches it on a normal path.

**Name resolution uses targeting too.** `wear()` and `remove()` accept a string and match it with
`f_key_matches` over the wearer's own contents, so the name test is a filter like every other rather
than a search of its own. The scope stops there — a room, a container on the floor or another character is the
command's problem, and it passes the object it resolved. See [design.md](design.md) § *Commands*.

## evennia-world-builder

**No coupling.** Neither library imports the other. World-builder creates objects from YAML; this
library is a set of mixins on typeclasses, so an authored item is equipment because of the typeclass
its prototype names, which needs nothing from either side.

**One thing to know, on a path neither library is aimed at.** World-builder writes authored attributes
with `obj.attributes.add()`, which goes to the attribute store and not through the descriptor — so a
`wearslot` set in YAML never reaches `WearslotProperty.at_set()` and is not validated. A malformed
declaration would land silently and surface later as an item that cannot be worn anywhere.

It takes an unusual combination to reach. World-builder authors the fixed world — rooms, exits,
fixtures and stationary NPCs — and a wearable item's slots are normally a class-level default on its
typeclass, which *is* validated. Both would have to be true at once: a game using `contents:` to author
portable equipment, and overriding `wearslot` per instance rather than leaving the typeclass to declare
it.

This is the general `.db` bypass rather than anything world-builder does wrong, and it is not fixable
from either library's side — see [../CLAUDE.md](../CLAUDE.md) § *Working conventions*. A game doing both
either accepts unvalidated declarations or checks them in its own build step.

`[TBD — needs discussion: whether world-builder should route authored attributes through the descriptor
where one exists. It would close this for every library with a validated `AttributeProperty`, not just
this one, and it is world-builder's call rather than ours.]`

## evennia-yaml-reader

**No coupling.** Neither library imports the other. yaml-reader depends only on `pyyaml`, has no
Evennia dependency and touches no database, so nothing it does is visible to this library and nothing
this library does is visible to it.
