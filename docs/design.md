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
Built once, then mutated — `wear()` assigns an item, `remove()` assigns `None`. Reads are a plain
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

**`wear(item, slot=...)` names a place.** Group order is the item author's preference, and preference
is not always what a player means: a shortsword declaring `[["WIELD"], ["HOLD"]]` goes to the wield
hand whenever that hand is free, so asking to *hold* it gets it wielded — and a ring always lands on
the first free finger rather than the one asked for. Naming a slot narrows the candidate groups to
those **containing** it, then selection proceeds unchanged.

Containing, not equal to: a group is taken whole, so a greatsword named by one hand still takes both.
The two refusals stay apart because the fixes differ — "you have no `DOG_NECK`" is about the wearer's
body, "the helmet cannot be worn on your `LEFT_HAND`" is about the item, and one message for both
would be wrong half the time.

A slot is given as an enum member or as its value. A consumer declares `body_slots` with members and
reads `worn_items` keyed by their values, so whichever the library demanded would be the other one to
somebody.

This is what makes `wield` and `hold` more than `wear` with a different word printed, and it opens a
command syntax the library does not otherwise reach — `wear ring on right finger`.

**`remove()` takes a slot too, and there it can stand alone.** Wearing nothing into a slot means
nothing, so `wear()` keeps its item required; taking off whatever is on the right finger is a complete
instruction, so `remove(slot=...)` needs no item.

| Call | Means |
|---|---|
| `remove("ring")` | the worn items matching, first if they share a key |
| `remove("ring", slot="RIGHT_FINGER")` | that item, and only if it is in that slot |
| `remove(None, slot="RIGHT_FINGER")` | whatever is in that slot |
| `remove()` | neither — refused rather than guessed at |

**Two identical rings is what the argument is for.** `Which ring do you mean?` has no answer a player
can give when both keys are the same, so naming the slot is the only way to say which hand. Nothing
else on the surface reaches it.

Which decides how the two arguments combine: given both, **the string confirms what is in the slot**
rather than being resolved on its own. Resolving independently returns the first of the two rings and
then fails the identity check against the slot — refusing the exact call the argument exists to serve.

## Four hooks around wearing

| Hook | Returns | Fires |
|---|---|---|
| `at_pre_wear(item)` | `(bool, str)` | after the ordinary refusals, before a slot is chosen |
| `at_post_wear(item, slots)` | nothing | after the slots are written, on success only |
| `at_pre_remove(item)` | `(bool, str)` | before anything is freed |
| `at_post_remove(item, slots)` | nothing | after the slots are freed, on success only |

The library refuses nothing of its own in any of them.

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

What happens when a consumer's command calls `wear(item)`. No gaps.

- **[game]** the command resolves what the player named, using Evennia's search
- **[game]** the command calls `caller.wear(item)`
- **[library]** the item is refused unless it is in `contents` and not already worn
- **[library]** the item's `wearslot` groups are read; an item declaring none is refused
- **[library]** each group is tested — every slot in it must exist on this wearer and be free
- **[library]** the first whole group that passes is filled, all slots at once
- **[library]** `(True, message)` goes back, or `(False, why not)`
- **[game]** the command speaks

Selection completes before anything is written. Nothing moves: the item was in `contents` before and
is in `contents` after, so the carried weight does not change.

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
- **[library]** `contents` is walked and anything whose identity is in the record is worn
- **[library]** one `(bool, str)` per attempt comes back, refusals included

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

**Four live in `contrib/`** — `wear`, `remove`, `equipment`, `inventory`. The test in the standards is
whether core is fully functional without the folder, and it is: the mixins are complete, and a consumer
driving `wear()` from their own code loses nothing.

They ship because Evennia has no vocabulary for slots, so a consumer would otherwise have a mechanism
no player can reach. Only `inventory` replaces anything of Evennia's; the other three are new words,
and Evennia merges cmdsets by key, so no explicit removal is needed.

**`wield` and `hold` are not among them.** They are a game's vocabulary rather than a mechanism: they
only mean something where an item's natural slot differs from where a player sometimes wants it, and
their slot names come from a consumer's enum. The capability stays reachable without them —
`wear sword on wield` does everything `wield sword` does — so a game that wants the shorthand writes
two short subclasses.

`get`, `drop` and `give` are not among them either, and need not be. Evennia's `CmdGet` calls
`obj.move_to(caller)`, so `at_pre_object_receive` already fires and the stock commands respect a
refusal untouched.

**They are replaced wholesale, not extended.** No display hooks, no seams. A consumer wanting different
output overrides `func()` — which is what FCM will do, since almost all of its inventory rendering is
its own: fungible balances interleaved with the items, gold, encumbrance, condition labels, and what a
blind character can make out. Five seams to share fifteen lines of stacking logic is a poor trade, and
each seam is a shape the next consumer has to fit. A seam gets added when a second consumer asks for
one, and it will be the right seam because someone will have said where it goes.

**They render like a MUD, not like a debug dump.** Colour, aligned columns, slot names title-cased.
FCM's `equipment` and `inventory` are the benchmark:

```
Equipped Items

  <Head>        a leather cap  (worn)
  <Left Hand>   a shortsword   (pristine)
  <Right Hand>
```

What contrib cannot do is anything reading a game's own attributes — condition labels, visibility,
balances. Those are why a consumer replaces the command rather than configures it.

### Naming a slot from typed text

`wear ring on right finger` needs the player's words turned into a slot name. Two helpers in
`contrib/utils.py` do it, and both are contrib's because **core never sees typed text** — its methods
take a slot name or an enum member.

`normalise_slot(text)` reduces a string to one comparable form: upper case, with spaces, underscores
and hyphens removed. **Both sides go through it**, which is the point — it stops mattering how a
consumer spelled the enum, so `RIGHT_FINGER` and `RIGHTFINGER` both answer to every spelling a player
might type. The result is for comparison only; what reaches `wear()` is the real value.

Normalising cannot insert a separator — nothing in `backpack` says where the word breaks — so stripping
them is what makes all four spellings work. The cost is that a game naming both `BACK_PACK` and
`BACKPACK` makes them permanently ambiguous. That is a naming mistake rather than something to design
around: two slots differing only by a separator are two a player could never reliably name.

`match_slot(wearer, text)` returns `(slot_name, None)` or `(None, refusal)` — the shape
`_resolve_wearable()` uses, so a command reads the same for items and slots. An exact match wins
outright, which a game with both `HAND` and `LEFT_HAND` needs; failing that, a substring, which is one
answer or a question.

It matches **this wearer's slots, not the whole enum**, so a humanoid asking for a dog neck is told it
has none rather than told it is ambiguous, and a one-fingered creature is never asked which finger.

Three refusals, and the difference between them is what a player has left to go on:

```
Which slot? Type 'equipment' to see your wear slots.
You have no foot. Type 'equipment' to see your wear slots.
Which do you mean — left hand or right hand?
```

The first two leave a player with nothing, so both name the command that answers it. The third does
not, because the options are already in the message. All three are verb-agnostic — `remove from right
finger` uses the same matcher, so nothing here may assume wearing.

Ambiguous slots are listed where ambiguous **items** are not. A name match could run to five and the
list would be noise; a wearer has ten slots in total and a substring rarely hits more than two, so
naming them tells the player exactly which words work.

### What a command actually does

`CmdWear` is about twenty lines, and none of them decide anything:

```
wear <item>
wear <item> on <slot>
```

1. Refuse an empty argument.
2. Split on the **last** ` on `.
3. If a slot was named, match it — **before** `wear()` is called, so a mistyped slot never puts the
   item on somewhere else first.
4. Call `wear()`, and say what it returns.
5. On success, tell the rest of the room.

Every refusal a player sees comes from the mixin or the matcher **verbatim**, so "you are already
wearing that" has one wording however a player reached it.

`CmdRemove` is the same shape, splitting on ` from ` and with one form wearing has no counterpart to:

```
remove <item>
remove <item> from <slot>
remove from <slot>
```

**Both split through `split_argument(text, keyword)`**, which pads the string before splitting on the
**last** occurrence. Last, not first, because an item may contain the word — *a ring on a chain* — and
splitting on the first would take the chain for a slot.

The padding is what makes the edges ordinary. `remove from right hand` has no item and
`remove helmet from` has no slot, and a split needing a space each side of the keyword would miss both
— so the item-less form needs no branch of its own, and a trailing keyword resolves to an empty slot
rather than being swallowed into the item's name.

The cost of splitting at all is that `wear ring on a chain`, with no slot meant, reads the chain as one
and refuses. Nothing in the string says which was intended, so the rule is not to put ` on ` or
` from ` in a wearable's name — the letters are fine, it is the spaced word that splits, so *an onyx
ring* and *a bone helm* are safe.

The room broadcast excludes the caller. Without that they receive the mixin's message and the rendered
broadcast, which read identically — "You wear iron helmet." twice.

### Reading a slot sheet

`CmdEquipment` lists every slot the wearer has, in `body_slots` order, with what is in it:

```
Equipped Items

  <Head>        an iron helmet
  <Body>
  <Left Hand>   a greatsword
  <Right Hand>  a greatsword
```

**The item is named through `get_display_name(caller)`**, which is Evennia's own viewer-aware hook. A
game whose items read differently in the dark overrides that once and gets it here, in `look`, and
everywhere else. A seam of ours would be a second and worse version of the same thing — so this
library provides none, and that is the answer for `inventory` too.

The boundary is worth knowing: per-item naming is covered, whole-listing behaviour is not. A game that
renders *every* line as "Something" when the looker is blind is making a decision about the listing,
which no per-item hook can express, and overrides the command.

**The column width is computed** from the longest slot name this wearer has, so a body plan naming a
`LEFT_SHOULDER_PAULDRON` still aligns. The gap after it is `slot_column_gap`, a class attribute rather
than a module constant — a game widens it by subclassing, and nothing in contrib declares a constant
that would belong in core's `config.py`.

**An empty slot shows its name and nothing else.** The absence is the information, and a word for it
would be noise on every line a player has not filled.

**A multi-slot item appears under every slot it fills.** A greatsword beside both hands reads oddly,
but `worn_items` genuinely holds it twice and showing it once would leave a hand looking free.
Collapsing it is a judgement about wording, which belongs to whoever replaces the command.

**The mixin resolves the name, so the command does not.** `wear()` and `remove()` each take a string
or an object, and a string is matched against what the wearer holds with `f_key_matches` — the same
filter path as everything else the library walks.

The alternative made every command do the work twice. A command handed only objects has to filter the
wearer's contents to find one, and then `wear()` filters again to confirm what the caller just
established. Resolving inside means it happens once, and the command is three lines:

```python
worn, message = caller.wear(self.args)
caller.msg(message)
```

An object is still accepted, because `restore_worn()` and a consumer equipping something it has just
created both hold one already — and two identical rings are distinct objects but the same string.

**Each searches its own half, in two passes.** `wear()` looks at the unworn items first, `remove()` at
the worn ones. The second pass is what makes the refusal useful: a single pass tells someone already
wearing the helmet that they are not carrying it, and tells someone holding the boots that they have no
such thing. Both are false, and neither helps.

| | First pass | Second pass says | Nothing matched |
|---|---|---|---|
| `wear()` | not worn | "You are already wearing X" | "You are not carrying `<text>`" |
| `remove()` | worn | "You are not wearing X" | "You are not carrying `<text>`" |

**Several matches are two different situations.** Items sharing a key are interchangeable, so the first
is taken — asking which of two identical rings is meant has no answer a player can give. Differing keys
are a real question, and the reply quotes what was typed rather than listing candidates, which could
run to five.

**The scope is what the wearer holds, and nothing wider.** Rooms, containers on the floor and other
characters are the command's problem, and a command wanting one of those resolves it itself and passes
the object.

## Not yet decided

Nothing. The mechanism is complete, and the four commands are agreed in shape and unwritten — work
rather than an open question.

Two things that were open here are settled above: the commands render, and they are replaced wholesale
rather than configured; and the gate on wearing is on the wearer, `at_pre_wear()`, with no item-side
counterpart — a consumer wanting one delegates to the item in a line.
