# Design

How the library is put together and why. Covers the whole mixin family, including the parts not built
yet — each section says which. Behaviour is agreed in [test-plan.md](test-plan.md) first; this holds
the reasoning that spans more than one case.

## The mixin family

Four mixins, two pairs. Each pair is a base and a specialisation, and the item side mirrors the carrier
side.

| Carrier side | Item side | Declares |
|---|---|---|
| `EquipmentCarryingMixin` | `EquipmentCarriableMixin` | `weight` |
| `EquipmentWearslotsMixin(EquipmentCarryingMixin)` | `EquipmentWearableMixin(EquipmentCarriableMixin)` | `wearslot` |

**Built:** all five. `EquipmentContainerMixin` takes both sides of the first pair. What remains is
recovery after an archive, and the commands.

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

A consumer declares their body plans in one module, named by one setting:

```python
EQUIPMENT_WEARSLOTS = "world.wearslots.LAYOUTS"       # settings.py

LAYOUTS = {                                            # world/wearslots.py
    "humanoid": ["HEAD", "BODY", "LEFT_HAND", "RIGHT_HAND"],
    "dog": ["DOG_NECK", "DOG_BODY"],
}
```

A typeclass names which one it uses — `wearslot_layout = "humanoid"` — and the mixin derives its slots
from it on every read. **Only what is occupied is stored.** A slot added to a layout is therefore
usable by characters that already exist, once the server restarts; a stored slot dictionary would
leave them without it for good.

The layouts resolve once per process. Nothing can change a setting while the server is up, so there is
nothing to invalidate.

An item declares its slots as a **list of groups** — each group one option, every slot in a group
taken together. `wear()` walks the groups in order and takes the first where every slot both exists on
this wearer and is free.

That one test does two jobs. A collar declaring `DOG_NECK` fails it on a humanoid for the same reason
a helmet fails it when the head is taken, so creature-type restriction needs no code of its own — and
a two-handed weapon declaring `[["WIELD", "HOLD"]]` cannot be equipped alongside anything in either
hand, so `two_handed` needs no flag, no command checks and no display note.

**Selection completes before anything is written.** Filling slots while checking them would leave a
two-handed item in one hand when the other turned out to be occupied.

`get_all_worn()` and `get_carried()` are both built by walking `contents`, not the slot map. That
deduplicates a multi-slot item, keeps a deleted object from reappearing, and makes the two a partition
— they differ by one `not`, so nothing a wearer holds can fall through both.

## Commands

**All six live in `contrib/`** — `wear`, `remove`, `wield`, `hold`, `equipment`, `inventory`. The test
in the standards is whether core is fully functional without the folder, and it is: the mixins are
complete, and a consumer driving `wear()` from their own code loses nothing.

They ship because Evennia has no vocabulary for slots, so a consumer would otherwise have a mechanism
no player can reach. They render plainly and are meant to be read and replaced — a consumer wanting
different wording subclasses one rather than reimplementing the mechanism behind it.

`get`, `drop` and `give` are not among them and need not be. Evennia's `CmdGet` calls
`obj.move_to(caller)`, so `at_pre_object_receive` already fires and the stock commands respect a
refusal untouched.

**The library resolves no names.** Finding the object a player typed at is the command's job, using
Evennia's own `search`. Doing it in the mixin would mean depending on a targeting system — which is
also why there is no coupling with `evennia-targeting`.

## Not yet decided

- Recovery after an archive. A restored character has an empty slot map and items with new primary
  keys, so what was worn has to be recorded against a durable identity the consumer supplies. Agreed
  in shape — a set of identities, rebuilt from what is worn, and a `restore_worn()` that walks
  `contents` — and unwritten.
- Whether anything may refuse to come off. `wear()` has gates; `remove()` has none.
- Whether the library renders equipment displays or returns data for the consumer to format. Both of
  FCM's hard imports live in its render methods.
- The item-side gate a consumer overrides to refuse an item, and its default.
