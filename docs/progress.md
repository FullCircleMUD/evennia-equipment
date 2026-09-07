# Progress

Running log of milestones with links to evidence. Reverse chronological — newest first.

## 2026-09-07 — wear() takes a named slot

`wear(item, slot=...)` puts an item somewhere in particular. 195 tests.

- **Group order is a preference, and a player does not always mean it.** A shortsword declaring
  `[["WIELD"], ["HOLD"]]` goes to the wield hand whenever it is free, so asking to hold it gets it
  wielded. A ring always lands on the first free finger rather than the one asked for. Case `WE-23`.
- **Naming a slot narrows to the groups containing it**, not to the slot alone, so a greatsword named
  by one hand still takes both. Case `WE-24`.
- **Two refusals, kept apart.** "You have no `DOG_NECK`" is about the wearer's body; "the helmet
  cannot be worn on your `LEFT_HAND`" is about the item. Cases `WE-25`, `WE-26`.
- **An enum member or its value.** `body_slots` is declared with members and `worn_items` is keyed by
  their values, so whichever the library demanded would be the other one to somebody. Case `WE-28`.

`WE-23` is the case that separates a real implementation from one that merely checks the named slot
is free. Both hands empty and `LEFT_HAND` declared first, the ring has to land on the right one.

This is what makes `wield` and `hold` more than `wear` with a different word printed, and it reaches a
command syntax nothing else here does — `wear ring on right finger`.

## 2026-09-07 — remove() resolves a name too

The mirror of the change below, and the last method on the surface that had the problem. 188 tests.

- **`remove()` takes a string or an object**, resolved against what the wearer has on. Cases `RM-14`
  onward, one for one with `WE-14` onward.
- **The second pass says something different**, and that is the whole reason it exists: a string
  matching only a carried item answers "you are not wearing the iron helmet" rather than "you have no
  such thing". Case `RM-18`.
- **Nothing matched says "not carrying"** in both methods, since the wearer genuinely has no such
  thing. That is what makes the two refusals distinguishable.

Two `RM` cases passed the moment they were written, which was the tell in both directions. `RM-18`
matched the item's full key, so the existing "you are not wearing iron helmet" satisfied it without the
carried pass ever running — searching `"iron"` and demanding the message name *helmet* is what made it
discriminate. `RM-17` asserted only that the typed word came back, which both refusals do.

An audit of the rest of the surface found nothing else to convert. `is_worn()` and `at_pre_remove()`
take objects a caller already holds, the Evennia hooks are handed theirs by the engine, and
`can_carry()` takes a number.

## 2026-09-07 — wear() resolves a name

`wear()` takes a string or an object. 179 tests.

- **The redundancy is what decided it.** A command handed only objects filters the wearer's contents to
  find one, then `wear()` filters again to confirm what the caller just established. Resolving inside
  means it happens once, and the command drops to three lines.
- **An object is still accepted.** `restore_worn()` and a consumer equipping something it has just
  created both hold one, and two identical rings are distinct objects but the same string. Case
  `WE-22`.
- **Two ordered passes**, unworn contents first. A single pass tells someone already wearing the helmet
  that they are not carrying it, which is false and useless. Cases `WE-18`, `WE-21`.
- **Matching is `f_key_matches`** from targeting — case-insensitive substring over key and aliases, so
  `wear doom` reaches a *slaying helm of mega doom*. Cases `WE-14`–`WE-16`.
- **Several matches are two situations.** One key among them is an answer, so the first is worn.
  Differing keys are a question, and the reply quotes what was typed — `Which iron do you mean?` — since
  listing candidates could run to five. Cases `WE-19`, `WE-20`.

`WE-20` passed the moment it was written, which was the tell. `wear("iron")` fell through the existing
contents check and returned "you are not carrying iron" — false, and containing the word, so both
assertions held for the wrong reason. Requiring the message to *ask* is what made it discriminate.

Principle 6 changes with it: the library resolves a name against what the wearer holds. Rooms,
containers and other characters stay the command's problem.

## 2026-09-07 — filtering moved onto evennia-targeting

Every walk over an object's `contents` now goes through `walk_contents`. The library holds no inline
comprehension over `contents`. 170 tests.

- **`evennia-targeting` is a hard dependency**, declared in `pyproject.toml` and imported
  unconditionally by `carrying.py` and `wearslots.py`.
- **Two filters published** in `src/evennia_equipment/targeting.py` — `f_worn_by(wearer)` and
  `f_identity_in(identities)`. The module name is the convention every library extending targeting
  follows, so `find . -name targeting.py` shows what already exists. Cases `TG`.
- **Factories, not predicates.** Each closes over data read once — the occupied slots, the record —
  rather than recomputing it per object in the walk. `TG-07` fixes the snapshot semantics that implies,
  since the live-view reading is just as plausible.
- **`get_carried()` needs no filter of its own** — `op_not(f_worn_by(wearer))` is the exact complement,
  so one definition covers both halves.
- **The weight rebuild needed nothing new.** `f_excluding` already means "everything but this one". It
  refuses empty arguments, so a rebuild with nothing to exclude passes no filter rather than an inert
  one.
- **`TG-01` and `TG-08` run targeting's own `validate_factory`** over our filters, so the sibling's
  contract is checked by the sibling's code rather than by a copy of it that can drift.

`TG-12` is a deliberate divergence from targeting's convention that a factory built with nothing raises
`ValueError`. There, empty arguments can only be a caller bug; here an empty record is the ordinary
state of a wearer who had nothing on, and `restore_worn()` reaches it on a normal path.

The refactor changed no case. `GW`, `GC`, `RW` and the weight cases assert on results rather than on
how the walk is done, so they were the proof that the wiring swap was behaviour-preserving.

## 2026-09-07 — equipment survives a world rebuild

The mechanism is complete. 158 tests.

- **Two required settings**, both refused at boot and reported together — `EQUIPMENT_WEARSLOTS` and
  `EQUIPMENT_IDENTITY_ATTRIBUTE`. Collection came back because two independent settings can both be
  wrong; within the enum's own checks the sequence still short-circuits. Cases `CF-14`–`CF-18`.
- **`wearslot_identity` on the item** reads the attribute the setting names. `None` is not a failure —
  such an item is worn perfectly well and simply cannot be restored, because there is nothing to match
  it by. Cases `ID`.
- **`update_worn_equipment_record()`** writes the identities of what is worn to a persisted attribute.
  Rebuilt rather than appended to, so an item taken off since the last call is not in it. Cases `ER`.
- **`restore_worn()`** walks `contents` and wears anything whose identity is in the record, returning
  one `(bool, str)` per attempt straight from `wear()`. Order does not matter — the items all fitted
  at once when the record was written. Cases `RW`.
- **`at_pre_remove()`** is the one gate on removal, allowing by default. On the wearer rather than the
  item: a curse is the item's business, but "you are paralysed" is the wearer's, and an item-side hook
  could not express it. Cases `RM-10`–`RM-13`.

`RW-06` was written after the implementation, not before, and it earned its place: `restore_worn()`
read `item.wearslot_identity` on everything in `contents`, and a character carrying a rock crashed.
`getattr` with a default is the fix.

The record is the one thing in this library that is written down rather than derived. Everything else
rebuilds from live state; this has to survive the moment its source is destroyed.

`docs/installing.md` arrives with the standard that now requires it — eight numbered steps, the two
required settings, and what `check_settings()` cannot catch.

## 2026-09-07 — one enum instead of a layouts mapping

The wearing half was reworked. Slot names now come from a single consumer-declared `Enum`, and a
subclass per body plan names which of them that creature has. 133 tests.

- **`EQUIPMENT_WEARSLOTS` names an enum**, not a mapping of layouts. The boot check drops from seven
  guards to four — a bare-string layout, a non-string entry, a repeated name and an empty layout are
  all impossible in an enum. Cases `CF`, down from thirteen to eight.
- **A subclass per body plan** — `body_slots = (WearSlot.HEAD, ...)` — replaces a `wearslot_layout`
  key naming an entry in a settings dict. This is FCM's own shape, and it deleted the layout key, the
  derived slot dictionary, the reconciliation-on-read and the settings-based indirection with it.
- **`__init_subclass__` checks the declaration at import**, which is the earliest the library can see
  a typeclass — nothing at boot can enumerate them. Four refusals, each naming the class and the slot.
- **`worn_items` is a real stored dictionary**, built once and mutated. `at_init()` reconciles it
  against `body_slots` once per load and returns without writing when they match. Cases `WS`.
- **Identity, never equality.** `RM-09` was written on a hunch and failed twice: `remove()` compared
  with `==`, and then `is_worn()` did too, so `wear()` was refusing a second identical ring as already
  worn. Four call sites now compare by identity, and `get_all_worn()` / `get_carried()` key a set on
  `id()` rather than the objects, since a set uses `__hash__` and `__eq__` — both of which a
  consumer's typeclass may define. `GW-06` and `GC-06` were mutation-checked to prove they are not
  vacuous.
- **`_occupied_ids()` filters on `is not None`, not truthiness.** A consumer's typeclass defining
  `__bool__` — an empty container — would otherwise have a worn item appear in the inventory.

The rework was done as a checklist: the `Test function` column was cleared for all 65 affected cases,
then each prefix was reviewed, retired or reframed, its tests updated and its link refilled. The
linter reported the remaining work from both ends throughout.

## 2026-09-06 — slots, wearing and removing

`EquipmentWearableMixin` and `EquipmentWearslotsMixin` are built and tested. 129 tests.

- **Layouts come from one setting naming one module**, per the standards' consumer-authored config
  rule, and are refused at boot when unusable — missing, unresolvable, not a mapping, a layout given
  as a bare string, holding a non-string, repeating a name, or declaring no slots at all. Cases `CF`.
- **Slots are derived, not stored.** Only occupied slots are persisted; the slot list is read from the
  layout every time, so a slot added to a layout is usable by characters that already exist. Cases
  `WS`.
- **The layouts resolve once per process.** Nothing can change a setting while the server is up, so
  there is nothing to invalidate.
- **An item declares a list of groups** — each group one option, every slot in a group taken together.
  Validated in `at_set()` for shape and for names that appear in some layout. Cases `WR`.
- **`two_handed` and creature-type checks both disappear.** A greatsword declares
  `[["LEFT_HAND", "RIGHT_HAND"]]` and a collar declares `DOG_NECK`; the same "does this wearer have
  the slot, and is it free" test handles both. Cases `WE-02`, `WE-06`.
- **Selection completes before anything is written**, so a blocked group cannot leave an item half
  equipped. `WE-05`.
- **`get_all_worn()` and `get_carried()` walk `contents`, not the slot map** — which deduplicates a
  multi-slot item, keeps a deleted one from reappearing, and makes the two a partition. Cases `GW`,
  `GC`.

`isinstance(value, list)` is unsafe for an `AttributeProperty` holding a mutable: Evennia runs a
class-level default through `from_pickle`, which returns a `_SaverList`, and that is not a `list`
subclass. `WR-09` caught it — the check refused a correct declaration made the way every consumer
will make one. `Sequence` is the right test.

Not built: recovery after an archive, and the commands.

## 2026-09-06 — the container

`EquipmentContainerMixin` is built and tested. 67 tests. Twelve lines of code, because the seam was
already there.

- **It takes both mixins** — a container is carried and carrying at once, and the two share no
  members.
- **`effective_weight` returns its own weight plus its contents.** A carrier already asks every object
  for that, so nothing in `EquipmentCarryingMixin` changed to accommodate containers.
- **A rebuild forwards upward** — `_recalculate_item_weight()` calls `at_weight_changed()` after
  `super()`, so a holder's total follows what happens inside a bag it is carrying.
- **The walk upward needs no termination guard.** A character is not carriable and a room does not
  carry, so the chain runs out on its own. `CN-07` and `CN-08` prove it, and a failure there would have
  been a loop rather than a wrong number.
- **Coin in a purse counts, unplanned.** `effective_weight` reads `current_weight_carried` rather than
  `items_weight`, so `extra_weight()` is included and a container never learns balances exist.
  `CN-12`.
- **The panniers case is a subclass**, not a flag — `effective_weight` returning `self.weight` alone.
  A boolean would say there are exactly two modes. `CN-13`.

`CN-14` aimed at the `at_init` risk — a container rebuilding on load notifies its holder, which reads
back in while Evennia is still constructing objects. It came out clean.

Not built: the wearing pair.

## 2026-09-06 — the weight half

`EquipmentCarriableMixin` and `EquipmentCarryingMixin` are built and tested. 54 tests.

- **`EquipmentCarriableMixin`** — `weight`, `effective_weight` and `at_weight_changed()`. Weight is a
  number, `int` or `float`, `>= 0`, coerced to `float`, validated in `at_set()`. Booleans refused,
  since `bool` subclasses `int` and would otherwise store as `1.0`. Cases `CR`, `EW`, `WC`.
- **`EquipmentCarryingMixin`** — the rebuild, the four things that trigger it, capacity, and the
  queries over it. Cases `CA`, `PR`, `RC`, `LV`, `IN`, `TW`, `CP`.
- **The rebuild has four triggers** — arrival, departure, load, and a held object's weight changing.
  A rebuild rather than an adjustment because `obj.delete()` fires no hook at all; see
  [design.md](design.md).
- **Nothing derived is cached.** `extra_weight()` and `extra_capacity()` are computed on read, so a
  currency balance or a strength potion needs nothing recalculated and no notification the consumer
  could forget to send.
- **The sum reads `effective_weight`**, so `EquipmentContainerMixin` will be an override of one
  property rather than a branch in the sum.
- **Capacity defaults to `float("inf")`** — unlimited, with no special case in any query, and no
  balance number invented on a game's behalf.
- **First caller of the log shim** — a refused arrival writes a `WARN` naming the object and why,
  since an aborted move reports nothing to whoever attempted it.

`PR-01` and `PR-03` were checked by mutation rather than trusted: removing the mixin check killed
`PR-01` and `PR-04` and left `PR-03` standing, and ignoring `super()`'s refusal killed `PR-03` alone.

`nohome=True` on every object the suite creates: Evennia's default home is `#2`, which this suite never
builds, and the foreign key is checked when the test transaction closes. Setting `DEFAULT_HOME = None`
instead looks equivalent and breaks `delete()`, which calls `.lstrip("#")` on it.

Not built: the wearing pair and `EquipmentContainerMixin`.

## 2026-09-06 — scaffold

The repo is set up to [library-standards.md](../../../design/library-standards.md) and the test runner
reaches the package. No library code.

- **Package, runner and test infrastructure** — `src/evennia_equipment/`, `runtests.py`,
  `tests/test_settings.py`. Two scaffold cases pass: the package imports and carries a version, and
  the log shim is a silent no-op outside an Evennia engine.
- **The log shim** — `equipment_log`, writing to `equipment.log`, copied verbatim from
  `evennia-message-bus` with the name and filename changed.
- **No tables, no alias, no router.** What is worn and what is carried is state on a character and
  belongs in the consumer's game database. Recorded as a ruling in [../CLAUDE.md](../CLAUDE.md).
- **Documentation surfaces** — `README.md`, `CLAUDE.md`, and this wiki with its index, test plan and
  interoperability statement.

What is not here: the equipment and carrying machinery itself. It is in FullCircleMUD, described in
that project's `design/inventory-equipment.md`, and the extraction has not started. The line between
what is library mechanism and what stays FCM content is open — see the `[TBD]` in
[../CLAUDE.md](../CLAUDE.md).
