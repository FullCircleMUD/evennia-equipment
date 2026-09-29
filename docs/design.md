# Design

How the library is put together and why. The mechanism is complete; the commands are not written.
Behaviour is agreed in [test-plan.md](test-plan.md) first; this holds the reasoning that spans more
than one case.

## The mixin family

Four mixins, two pairs. Each pair is a base and a specialisation, and the item side mirrors the carrier
side.

| Carrier side | Item side | Declares |
|---|---|---|
| `EquipmentCarryingMixin` | `EquipmentCarriableMixin` | `weight` |
| `EquipmentWearslotsMixin(EquipmentCarryingMixin)` | `EquipmentWearableMixin(EquipmentCarriableMixin)` | `wearslot` |

**Built:** all five, and equipment recovery with them. What remains is the commands.

The specialisation inherits rather than composes, so a consumer makes one decision per class — *worn,
or only carried* — and a wearable cannot be declared without the weight contract it depends on.

**Carrying is the base; wearing is a specialisation.** A game can have carrying without wearing, never
the reverse. That is a deliberate scope claim — do not split the pairs apart on the grounds that the
two mechanisms are independent. Their arithmetic is; the API is coupled on purpose.

## Coupling — hooks, not imports

Every game concept the library needs reaches it **through the object**, never through an import.
Restrictions, durability, stat effects and ownership all arrive that way: the library asks the item,
and the item answers however its game decides. This is `evennia-archive`'s principle 4 — *test the
object, never the library*.

**A hook earns its place only if the library works without it being overridden.** Otherwise it is an
abstract method, and the seam is in the wrong place.

## Filtering goes through evennia-targeting

Every walk over an object's `contents` is a `walk_contents` call with named filters. The library holds
no inline comprehension over `contents` anywhere.

The reason is that a filter written inline is a filter nobody else can find. "Is this item worn" is
needed by this library, by any command that lists an inventory, and by any game rule that cares — and
three copies of it are three places to fix when it is wrong. One definition, in the library that owns
the concept, is fixed once.

So the two filters this library needs are published rather than kept private, in
`src/evennia_equipment/targeting.py` — the module name every library extending `evennia-targeting`
uses, so `find . -name targeting.py` shows a reader what already exists before they write a second one.

| Filter | Matches | Used by |
|---|---|---|
| `f_worn_by(wearer)` | What that wearer has on | `get_all_worn()`, and inverted by `op_not` for `get_carried()` |
| `f_identity_in(identities)` | Items whose `wearslot_identity` is in a set | `restore_worn()` |

Both are factories, not predicates. Each closes over data assembled once — the occupied slots, the
record — instead of recomputing it for every object the walk visits, and the snapshot that produces is
the right semantics for a single pass.

The weight rebuild needs nothing of its own: targeting's `f_excluding` already expresses "everything
but this one", which is all `at_object_leave` wanted.

## Weight is rebuilt, not adjusted

`_recalculate_item_weight()` sums `contents` from scratch on every weight-changing event rather than
adding and subtracting as items come and go.

No set of hooks catches everything: `obj.delete()` does not fire `at_object_leave()` — in Evennia's
`objects.py` that hook is called only from `move_to()` — so an incremental total would keep a deleted
object's weight permanently. Rebuilding turns that into one stale reading. Hooks and rebuilding are a
pair; either alone leaves a defect.

Four things trigger it: an object arriving, an object leaving, the carrier being loaded into memory,
and a held object's weight changing. `exclude` exists for the second, because `at_object_leave` fires
*before* the object leaves `contents`.

The sum reads `effective_weight`, not `weight`. They are the same for a plain object; a container
overrides it to add what is inside. So the carrier never learns what a container is, and there is no
container branch in the sum — the container arrives as an override of one property.

## Stored, hook, read

The same shape on both sides of the comparison. A stored attribute holds what the library is told, a
hook supplies what it cannot see, and a property adds them when read.

| | stored | hook | read as |
|---|---|---|---|
| weight | `items_weight` | `extra_weight()` | `current_weight_carried` |
| capacity | `max_carrying_capacity` | `extra_capacity()` | `effective_capacity` |

**Nothing derived is cached, and that is the point.** Object movement fires Evennia hooks, so the
library sees it. A currency balance changing, or a strength potion, fires nothing — so a stored total
would need the consumer to notify us, and that call would eventually be forgotten. Computed on read,
there is nothing to go stale and no notification to miss.

Capacity defaults to `float("inf")`. It passes the same validator as any other non-negative number and
gives unlimited carrying with no "is it unlimited" branch in any query. A library that picked a real
number would be inventing a game's balance.

`can_carry()` and `is_encumbered` answer the question; they do not act on it. Refusing the move,
allowing it with a penalty, and ignoring it entirely are all reasonable, and none is the library's
call.

## A weight changing while the object is held

`WeightProperty.__set__` calls `at_weight_changed()` after storing, which tells the holder to rebuild.
Without it, an item enchanted lighter or a waterskin emptied would leave the holder's total stale
until something moved.

**The notification cannot live in `at_set()`.** That runs *before* the value is stored, so a rebuild
fired from there would read this object's old weight back out.

A consumer overriding the weight default must re-declare it as a `WeightProperty`. Re-declaring it as
a plain `NonNegativeNumberProperty` validates but does not notify, and nothing reports the difference.

## Validating what is stored

Rules that can be stated go in the `AttributeProperty`'s `at_set()`, not at each call site — see
[library-standards.md](../../../design/library-standards.md) § *Reading and writing object state*.

`weight` is a number, `int` or `float`, `>= 0`, coerced to `float`. Booleans are refused explicitly:
`bool` subclasses `int`, so a plain numeric check would store `True` as `1.0`.

`at_set()` fires only on assignment through the descriptor, so `obj.db.weight` bypasses it. That cannot
be closed from here — it is documented and pinned by `CR-11` rather than defended against.

## The container

A container is carried and carrying at once, so it takes both mixins and adds two things:

```python
@property
def effective_weight(self):
    return self.weight + self.current_weight_carried

def _recalculate_item_weight(self, exclude=None):
    super()._recalculate_item_weight(exclude=exclude)
    self.at_weight_changed()
```

The first is what a carrier already asks every object for, so nothing in `EquipmentCarryingMixin`
changes. The second forwards a rebuild upward, since a container's contribution moves whenever its
contents do.

**The walk upward ends without a guard.** A character is not carriable and a room does not carry, so
neither passes the check in `at_weight_changed()` and the chain runs out on its own.

**`current_weight_carried`, not `items_weight`** — so a container whose game tracks a balance
contributes coin as well as objects, through `extra_weight()`, without the container knowing balances
exist.

The panniers case — contents that do not count against whoever carries the container — is a subclass
overriding `effective_weight` to return `self.weight` alone. Not a flag: a boolean says there are
exactly two modes, and an override also serves "half the weight".

## Slots and wearing

**One enum names every slot the game will ever have**, declared by the consumer and pointed at by one
setting. It is the single list both sides are checked against — a wearer's slots and an item's
declaration — which is what makes a typo in either one reportable.

```python
EQUIPMENT_WEARSLOTS = "world.wearslots.WearSlot"  # settings.py

class WearSlot(Enum):                              # world/wearslots.py
    HEAD = "HEAD"
    BODY = "BODY"
    LEFT_HAND = "LEFT_HAND"
    DOG_NECK = "DOG_NECK"
```

**A subclass per body plan** names which of them that creature has:

```python
class HumanoidEquipmentMixin(EquipmentWearslotsMixin):
    body_slots = (WearSlot.HEAD, WearSlot.BODY, WearSlot.LEFT_HAND)
```

Enum members rather than strings, so a typo is an `AttributeError` on the line that wrote it. The
declaration is checked in `__init_subclass__` — when the class is defined, which is the earliest the
library can see it, since nothing at boot can enumerate a consumer's typeclasses.

`worn_items` is the storage: a real, persisted dictionary of slot name to the item in it or `None`.
Built once, then reassigned — `wear()` fills slots with an item, `remove()` sets them to `None`. Reads are a plain
attribute read, because a body plan changes when code changes, which is a restart.

`at_init()` reconciles the two once per load: it adds slots the class has gained and drops ones it has
lost, and returns without writing when the names already match. An item in a dropped slot simply stops
being worn — nothing moves, because a worn item never left `contents`.

An item declares its slots as a **list of groups** — each group one option, every slot in a group
taken together. `wear()` walks the groups in order and takes the first where every slot both exists on
this wearer and is free.

That one test does two jobs. A collar declaring `DOG_NECK` fails it on a humanoid for the same reason
a helmet fails it when the head is taken, so creature-type restriction needs no code of its own — and
a two-handed weapon declaring `[["WIELD", "HOLD"]]` cannot be equipped alongside anything in either
hand, so `two_handed` needs no flag, no command checks and no display note.

**Selection completes before anything is written.** Filling slots while checking them would leave a
two-handed item in one hand when the other turned out to be occupied.

**`slots_for(item, slot=None)` answers where an item would go; `wear(item, slot=None)` puts it there.**
The query changes nothing, so a command asks it, refuses on `None`, and only then calls `wear()` — which
asks it again, so the check and the placement cannot disagree.

**`slot` names a place.** Group order is the item author's preference, and preference is not always
what a player means: a shortsword declaring `[["WIELD"], ["HOLD"]]` goes to the wield hand whenever it
is free, and a ring lands on the first free finger. Naming a slot — an enum member — narrows the groups
to those **containing** it. Containing, not equal to: a group is taken whole, so a greatsword named by
one hand still needs both free.

**`remove(item)` takes only the item.** A slot identifies what to take off, so once the caller has the
item — by name, or read out of `worn_items[slot]` — a slot adds nothing. That is how a player picks
between two identical rings: `remove from right finger` reads the slot, and hands `remove()` the ring
in it.

## Four hooks around wearing

| Hook | Returns | Fires |
|---|---|---|
| `at_pre_wear(item)` | `(bool, str)` | inside `wear()`, after its guards, before anything is written |
| `at_post_wear(item, slots)` | nothing | after the slots are written, only when the item went on |
| `at_pre_remove(item)` | `(bool, str)` | inside `remove()`, after its guard, before anything is freed |
| `at_post_remove(item, slots)` | nothing | after the slots are freed, only when the item came off |

The library refuses nothing of its own in any of them.

**The pre hooks are the one decision inside `wear()` and `remove()`.** Everything else — finding the
item, checking it can go where asked — is settled by the caller before the call. The pre hooks are
different because they are how other components add their rules: a class restriction, a minimum
strength, a curse. Asking them inside the method means every path gets the veto, `restore_worn()`
included. A refusal comes back as `(False, reason)`, for the command to tell the player.

**Equipment changes a character, and the library cannot know how.** A ring of strength is worth nothing
until something recalculates the wearer's strength, and that has to happen on both edges. Nothing else
tells a game the worn set moved.

**The pre hooks are on the wearer, not the item.** A cursed item is the item's business, but "you are
paralysed", "your class cannot use that" and "not in combat" are the wearer's, and an item-side hook
could not express them. A consumer wanting item-side logic delegates to the item in one line; the
reverse is not available.

**The post hooks fire after the write.** A consumer recalculating from `get_all_worn()` sees the change
it was told about, rather than being handed an answer it then has to apply itself.

**They are given the slots.** At post-wear a consumer could read `worn_items` instead; at post-remove it
cannot, because the slots are freed by then and where the item sat is recorded nowhere else. Passing
them on both sides keeps the pair symmetrical rather than making one the exception.

`restore_worn()` goes through `wear()`, so a shard move puts the bonuses back with the gear. A restore
that filled the slots directly would leave a character wearing a ring of strength and no stronger for
it.

`get_all_worn()` and `get_carried()` are both built by walking `contents`, not the slot map. That
deduplicates a multi-slot item, keeps a deleted object from reappearing, and makes the two a partition
— they differ by one `not`, so nothing a wearer holds can fall through both.

## Identity, never equality

Everywhere the library asks "is this the object in that slot", it asks by identity. `is`, not `==`;
`id()` in a set, not the objects themselves.

A consumer's typeclass is free to define `__eq__` and `__hash__`, and comparing by key or by token id
is a reasonable thing for a game to do. Under equality, two rings that compare the same would break
three things at once: `wear()` refuses the second as already worn, `remove()` frees both slots, and
`get_carried()` drops the unworn one from the player's inventory.

Evennia's idmapper gives one Python instance per database row, so identity is exactly the right
question and `id()` is stable for as long as anything holds a reference.

## Booting, step by step

Every step from `django.setup()` to the library being usable, and who owns each — **[library]** for
this library, **[Evennia]** for Evennia or Django, **[game]** for the consumer. No gaps.

- **[Evennia]** `django.setup()` runs, which runs every installed app's `ready()`
- **[library]** `ready()` calls `check_settings()`
- **[library]** `EQUIPMENT_WEARSLOTS` is read; absent is a refusal
- **[library]** the path is resolved with `import_string`; a failure is a refusal with the cause chained
- **[library]** the result is checked: an `Enum`, with members, no repeated values, every value a string
- **[Evennia]** the server continues, or does not start at all
- **[game]** a typeclass module is imported later, on first use
- **[library]** `__init_subclass__` checks that module's `body_slots` against the enum

The two checks are deliberately in different places because they can be. The enum is settings, so it
is available at boot; a consumer's typeclasses are not enumerable from anywhere, so the earliest the
library sees one is the moment Python defines it.

## Picking something up, step by step

What happens when a player types `get sword`. No gaps — and note the library ships no command here,
because Evennia's already drives every hook it needs.

- **[Evennia]** `CmdGet` resolves the name and calls `obj.move_to(caller)`
- **[Evennia]** `move_to` calls `at_pre_object_receive` on the destination
- **[library]** the object is refused if it has no `EquipmentCarriableMixin`, and the refusal is logged
- **[library]** a refusal from anything further down the chain is passed on rather than overruled
- **[Evennia]** the move happens, or is aborted
- **[Evennia]** `at_object_receive` fires on the destination
- **[library]** the carried weight is rebuilt from `contents`
- **[Evennia]** `CmdGet` messages the room

Dropping is the same list with `at_object_leave`, which fires *before* the object leaves — so the
rebuild is told to exclude it.

## Wearing, step by step

What happens when a player types `wear ring on right finger`. No gaps.

- **[game]** the command's `resolve_wear()` splits the text and finds the item with `find_carried()`
  and the slot with `match_slot()`
- **[game]** the command asks `slots_for(item, slot)`, and refuses on `None`
- **[game]** the command calls `caller.wear(item, slot)`
- **[library]** an item not carried, already worn, or with nowhere free raises — the caller should have
  settled it
- **[library]** `at_pre_wear(item)` is asked; a refusal returns `(False, reason)`
- **[library]** the group is written, all its slots at once, and `at_post_wear(item, group)` fires
- **[library]** `(True, "")` goes back
- **[game]** the command speaks, tells the room, and runs anything it does on success

Nothing moves: the item was in `contents` before and is in `contents` after, so the carried weight does
not change.

## Recovering equipment after a rebuild, step by step

What has to happen for a character to come back wearing what they were wearing, after an archive and
restore — or, under `evennia-scaling`, after any move between instances. No gaps in the library; the
two `[game]` steps are the consumer's to wire up.

- **[game]** `update_worn_equipment_record()` is called before archiving
- **[library]** the identities of everything worn are written to `worn_equipment_record`
- **[game]** the character is archived, its items held wherever the game keeps them
- **[game]** the world is rebuilt; every primary key is reissued
- **[evennia-archive]** the character is restored, its slot assignments gone
- **[game]** the items are restored into `contents`
- **[game]** `restore_worn()` is called
- **[library]** `contents` is walked for anything whose identity is in the record
- **[library]** an item already worn, or with nowhere free, is refused; anything else goes through
  `wear()` into its default group, so `at_pre_wear` is asked
- **[library]** one `(bool, str)` per attempt comes back, refusals included, and refusals are logged at
  INFO — nothing is sent to the player

**Both `[game]` steps exist because the library cannot know when they happen.** Nothing it could hook
would tell it a game is about to archive, or that an asynchronous restore has finished — and hooking
either would mean learning that archiving exists, which is a sibling library's business, not ours.

The identity is the consumer's too, read from whatever `EQUIPMENT_IDENTITY_ATTRIBUTE` names. A
database key cannot serve, because the rebuild that makes recovery necessary is the same event that
reissues it.

**The record is written down, not derived.** Everything else in this library is rebuilt from live
state — weight from `contents`, slots from `body_slots`. This one cannot be: it has to survive the
moment its source is destroyed, which is the whole point of it. Persisted on the object, never `ndb`.

## Commands

**Four live in `contrib/`** — `wear`, `remove`, `equipment`, `inventory` — each as a mixin for a game to
compose onto its own command class, and as a concrete command over Evennia's `Command`:

```python
class CmdWear(CmdWearMixin, QueuedCommand):   # a game's own base
    key = "wear"
```

Core is complete without the folder: a game driving `wear()` from its own code loses nothing. They ship
because Evennia has no vocabulary for slots.

**A command decides, then executes.** `wear()` and `remove()` take an item already found, so the finding
is the command's. The helpers do it:

| Helper | Lives in | Does |
|---|---|---|
| `find_carried(caller, text)` | `finders` | the item named among what is carried and not worn |
| `find_worn(caller, text)` | `finders` | the item named among what is worn |
| `match_slot(caller, text)` | `finders` | typed text as one of the caller's slots, an enum member |
| `resolve_wear(caller, text)` | `contrib.utils` | `<item> [on <slot>]` as an item and a slot |
| `resolve_remove(caller, text)` | `contrib.utils` | `<item>`, `<item> from <slot>` or `from <slot>` as an item |

Each returns `(answer, None)` or `(None, refusal)` with a finished message, and messages no one. The
finders are core because carried and worn are this library's concepts — any command acting on a
player's inventory or equipment uses them, an `enchant` as much as a `wear`.

The finders match with Evennia's own `caller.search`, so aliases and `sword-2` work as in every other
command. `quiet=True`, so Evennia says nothing itself; `use_dbref=False`, because a `#dbref` makes the
search global and a builder would otherwise reach an object anywhere in the game. `match_slot` uses
`evennia_targeting.parse_match(..., substring=True)` over the caller's own slots, so a humanoid typing
`dog neck` is told it has none.

The split is `evennia_targeting.parse_split`, on the last whole-word `on` or `from`. An item whose name
holds the spaced word — *a ring on a chain* — needs the slot named to be worn by name.

**Five seams, each with one job.**

| Seam | On | Default |
|---|---|---|
| `announce(item)` | `wear`, `remove` | tells the room with `msg_contents`; a game with its own messaging overrides it |
| `at_success(item)` | `wear`, `remove` | nothing; a game whose equipping costs a turn starts its time wait here |
| `extra_lines()` | `inventory` | `[]`; a game's balances, placed between the items and the summary |
| `slot_column_gap` | `equipment` | `2`; the spaces after the slot column |
| `slot`, `verb` | `wear` | `None` and `wear`; a game's `wield` fixes the slot and words the lines |

`announce` and `at_success` run only when the item went on or came off. The room line names the item
found, not what was typed.

**`wield`, `hold`, `get`, `drop` and `give` are not among them.** `wield` and `hold` are a game's words
over its own slot names: `CmdWearMixin` with `slot` and `verb` set. Evennia's `get` and `drop` call
`move_to`, so `at_pre_object_receive` fires with no command of ours.

### Reading a slot sheet and an inventory

`equipment` lists every slot in `body_slots` order, with the item named through
`get_display_name(caller)` — Evennia's viewer-aware hook, so a game whose items read differently in the
dark gets it here for free. An empty slot shows its name and nothing else. A multi-slot item appears
under every slot it fills. The column width comes from the longest slot name.

`inventory` lists what is carried and **not** worn — Evennia's lists `contents`, and so shows a player
their armour as though it were in a sack. One `bucket_contents` walk filters and groups: a stackable
item's bucket is its key, an unstackable one gets its own. `stackable` is on the item, `True` by
default, because "is this the same as that" is the item's question. Stacking is by key, not displayed
name, so two different things a looker makes out as `something` stay two lines. The summary names a
limit only when there is one.

### One thing to merge

`EquipmentCmdSet` holds the four concrete commands:

```python
class CharacterCmdSet(default_cmds.CharacterCmdSet):
    def at_cmdset_creation(self):
        super().at_cmdset_creation()
        self.add(EquipmentCmdSet)
```

Added after the defaults, so our `inventory` replaces Evennia's by key. A game composing the mixins onto
its own commands adds those instead.

Consumer-facing detail is in **[contrib.md](contrib.md)**.

## Not yet decided

Nothing.
