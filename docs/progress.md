# Progress

Running log of milestones with links to evidence. Reverse chronological — newest first.

## 2026-09-11 — three log lines where nothing else witnesses

An inspection for unlogged failure paths found three, all on the archive-restore pipeline; everything
else that goes wrong is already loud — boot refusals raise, validation raises at the assigning line,
and command refusals reach the player. 282 tests.

- **Slot reconciliation logs INFO** — only when a body plan changed between loads, naming slots added
  and dropped and anything a dropped slot held. An item in a dropped slot stops being worn with no
  hook fired, so this line is what answers "my ring stopped working". Cases `WS-20`–`WS-22`.
- **A refused restore logs INFO** — the same refusal `restore_worn()` returns, made durable against a
  caller that discards the list. Cases `RW-07`, `RW-08`.
- **A worn item with no identity logs WARN at record time** — the one line at WARN, because a game
  calling the recovery surface means gear to be restorable, so an identity-less worn item says the
  identifying system is broken. The setting pointing at nothing skips every item, and this burst is
  the only signal before a restore comes back empty. Cases `ER-08`, `ER-09`.

The level rule the three settled: INFO is the game working as intended, recorded so a player's
question can be looked up; WARN and ERROR are kept for something actually or potentially wrong.

## 2026-09-11 — logging through evennia-logging-extension

`log.py` is now the standard three-line binding — `equipment_log = make_logger("equipment.log")` —
and the hand-rolled shim is gone. 275 tests.

- **`evennia-logging-extension` is a hard dependency**, declared in `pyproject.toml` and installed as
  an editable sibling checkout like targeting.
- **The call surface is unchanged** — same name, same `(message, level, trace)` signature — so
  `carrying.py` and the `PR-04` test needed nothing.
- **`SC-02` reworded**: "outside an Evennia engine is a silent no-op" is the extension's contract now,
  not this library's, so the case claims only that the shim binds and a call returns None without
  raising.
- **`interoperability.md` now covers every sibling including `fcm-*`**, per the standard; the preamble
  excluding them is gone.

Linter clean at zero errors, zero warnings; the `library-standards-auditor` passed the judgment layer
the same day.

## 2026-09-08 — the command set, and contrib is complete

`EquipmentCmdSet` bundles the four, and `docs/contrib.md` documents them. 275 tests.

- **Merging is by key**, and the set is added after Evennia's defaults, so `inventory` replaces its own
  rather than competing with it. Case `CS-02` — the one that fails invisibly, since a player types
  `inventory`, gets a listing, and it is the wrong one.
- **`CS-01` guards the gap nothing else would**: a fifth command written and not added to the set works
  perfectly, passes its own cases, and no player can reach it.
- **`docs/contrib.md`** covers installing the cmdset, each command, naming a slot, `extra_lines()`, and
  what is deliberately absent — `get`/`drop`/`give`, `wield`/`hold`, and anything reading a game's own
  concepts.

`CS-03` was vacuous as written: it handed `self.call()` a `CmdWear()` instance, so dropping the command
from the set left it green. It now takes the command from the character's merged cmdset, which is the
only path that proves the wiring. Second messaging-or-wiring case this session to need a mutation check
before it discriminated — `CW-07` was the first.

That completes contrib. What remains is adoption, which is a game repo's decision.

## 2026-09-08 — the inventory command, and stackable

`CmdInventory`, the last of contrib's four, and the core property it needed. 272 tests.

- **`stackable` on `EquipmentCarriableMixin`**, `True` by default and validated as a real `bool`. A
  game with durability sets it `False` on those items; the library never learns why. Cases `ST`.
- **It is on the item, not in the command.** "Is this the same as that" is an item's question, and a
  rule inside a listing could only compare names — which is exactly what fails to tell two longswords
  apart when one is chipped. Cases `CI-13`, `CI-14`.
- **Stacking is by key, not displayed name**, so a seen and an unseen copy stay two lines and a blind
  player reads the real groupings rather than one total. Case `CI-05`.
- **`extra_lines()` is contrib's one seam**, returning `[]`. A game's balances are more things being
  carried rather than a footer after them, so they sit between the items and the summary — a position
  no override of the rendering could reach. Case `CI-08`.
- **The summary omits the limit when capacity is unlimited**, which is the default and therefore the
  ordinary case. Case `CI-11`.

`CI-09` failed on a test artefact worth remembering: `create_object(location=...)` does not fire
`at_object_receive`, so the carried total is never rebuilt and the summary read `0.0`. The suite
already knew — `RC-02` rebuilds by hand — but a command reading a live total needs the real path, so
these tests create in the room and `move_to` the wearer, which is what picking something up does.

## 2026-09-08 — the equipment command

`CmdEquipment`, the third of contrib's four. 255 tests.

- **`get_display_name(caller)` names every item**, which is Evennia's own viewer-aware hook. A game
  with darkness overrides that once and this listing follows — so the library ships no display seam of
  its own, here or in `inventory`. Case `CE-05`.
- **The column width is computed** from the longest slot name the wearer has, so an unusual body plan
  still aligns. `slot_column_gap` is a class attribute, overridable by subclassing and not a module
  constant that would belong in core's `config.py`. Case `CE-08`.
- **An empty slot shows its name and nothing else.** Case `CE-03`.
- **A multi-slot item appears under every slot it fills**, because `worn_items` holds it twice and
  showing it once would leave a hand looking free. Case `CE-06`.

The `ShroudedHelmet` fixture landed above `Helmet` in `game_typeclasses.py` and took the whole suite
down with a `NameError` — 228 errors from one misplaced class. The file has grown enough that an
anchor chosen from an earlier reading is no longer where it was.

## 2026-09-08 — the remove command

`CmdRemove`, the second of contrib's four. 247 tests.

- **Three forms**, one more than wearing: `remove <item>`, `remove <item> from <slot>`, and
  `remove from <slot>`. The last is what the slot argument was added for — two rings with one key, one
  on each hand, and this is how a player says which. Case `CM-05`.
- **`split_argument(text, keyword)`** now does the parsing for both commands. It pads the string before
  splitting on the last occurrence, which turns both edges into ordinary splits: a leading keyword
  needs no branch, and a trailing one gives an empty slot rather than being swallowed into the item
  name.

`CM-07` caught a real defect. `remove iron helmet from ` reaches the command as `iron helmet from` —
Evennia's parser drops the trailing space — so a split needing a space each side saw no keyword and
read the whole thing as an item name.

`CmdWear` had the same flaw, unfound. `CW-06` passed only because that command had not called
`.strip()` before splitting, which is one edit away from failing the same way. The padding fixes both,
and the `startswith("from ")` branch written for the item-less form is gone with it.

## 2026-09-08 — the wear command

`CmdWear`, the first of contrib's four. 238 tests.

- **It decides nothing.** Parse, match the slot, call `wear()`, speak what it returns, broadcast. Every
  refusal reaches the player verbatim from the mixin or the matcher, so one wording serves however a
  player got there. Case `CW-03`.
- **The slot is matched before `wear()` is called**, so a mistyped slot never puts the item on somewhere
  else first. Case `CW-05`.
- **`rpartition`, not `partition`.** An item may contain the word — *a ring on a chain* — and splitting
  on the first would take the chain for a slot. Case `CW-08`.

`EvenniaCommandTest` boots against `tests/test_settings.py` with no gamedir, and `self.call(cmd, args,
caller=...)` takes our own wearer, so its `char1` is ignored and the existing fixtures do the work. A
throwaway probe against a stock Evennia command settled that before any case was written.

`CW-07` was vacuous as first written and is the reason to mutation-check a messaging case.
`self.call(..., receiver=)` returns only the receiver's output, so the assertion could see the room
being told and not the wearer being told twice — removing `exclude=[caller]` left the suite green. It
now makes a second call capturing the caller's own output and counts the phrase.

## 2026-09-08 — contrib begins, with the slot helpers

`contrib/` exists, holding the two helpers the commands need before any command is written. 230 tests.

- **`normalise_slot(text)`** — upper case, separators removed. Both sides go through it, so how a
  consumer spelled the enum stops mattering: `RIGHT_FINGER` and `RIGHTFINGER` both answer to `right
  finger`, `right_finger`, `Right-Finger` and `rightfinger`. Cases `NS`.
- **`match_slot(wearer, text)`** — exact hit wins, then substring, returning `(slot_name, None)` or
  `(None, refusal)`. Cases `SM`.
- **Exact wins** because a game with both `HAND` and `LEFT_HAND` would otherwise never be able to name
  `HAND`. The `Chimera` fixture pins it with `BODY` and `DOG_BODY`. Case `SM-04`.
- **It matches the wearer's slots, not the whole enum**, so a humanoid asking for a dog neck is told it
  has none, and a one-fingered creature is never asked which finger. Case `SM-07`.
- **Ambiguous slots are listed** where ambiguous items are not — a name match could run to five, a slot
  match rarely exceeds two, so naming them tells the player which words work.

Both live in contrib because **core never sees typed text**. The normaliser started in core on the
argument that a consumer writing their own commands would want it, which is the speculative-function
trap: no caller today. A boot check refusing separator-colliding enum names went the same way — a check
in core guarding a contrib-only matcher protects nothing when contrib is not installed.

The first cut declared the separator set as a module constant and tripped `constant_outside_config`.
Following that rule would have put a contrib-only constant in core, which is the same mistake in
smaller form; the replaces are inline instead. The rule as written has no answer for a contrib-only
constant.

## 2026-09-08 — four hooks around wearing

`at_pre_wear`, `at_post_wear`, `at_pre_remove` and `at_post_remove`. 214 tests.

- **Equipment changes a character, and the library cannot know how.** A ring of strength is worth
  nothing until something recalculates the wearer's strength, on both edges.
- **The post hooks fire after the write**, so a consumer recalculating from `get_all_worn()` sees the
  change it was told about rather than being handed an answer to apply itself. Cases `WE-33`, `RM-32`.
- **They are given the slots.** At post-wear a consumer could read `worn_items`; at post-remove it
  cannot, because they are freed by then and where the item sat is recorded nowhere else. Cases
  `WE-34`, `RM-33`.
- **Neither post hook fires on a refusal.** One that did would strip a ring's bonus from a character
  still wearing it. Cases `WE-35`, `RM-34`.
- **`restore_worn()` goes through `wear()`**, so a shard move puts the bonuses back with the gear.
  Case `WE-36`.

`WE-35` and `RM-34` first failed with `'DefaultObject' object has no attribute 'wear'`. A typeclass
defined **inside a test function** cannot be resolved by `create_object` — Evennia looks it up by import
path and falls back to `DefaultObject` without complaint. Both fixtures moved to
`tests/game_typeclasses.py`.

## 2026-09-08 — remove() takes a named slot too

`remove(item=None, slot=None)`, and the slot can stand alone. 204 tests.

- **Two identical rings is what it is for.** Same key, one on each hand: `remove ring` takes the first,
  and "which ring?" has no answer a player could give. The slot is the only way to say which hand.
  Case `RM-29`.
- **The slot stands alone**, unlike in `wear()`. Wearing nothing into a slot means nothing; taking off
  whatever is on the right finger is a complete instruction. Case `RM-23`.
- **Given both, the string confirms rather than resolves.** Case `RM-24` mirrors `WE-24` — naming one
  slot of a two-handed item frees both.
- **Two refusals for a slot**, as `wear()` has: "you have no right finger" is about the wearer's body,
  "you are wearing nothing on your right finger" is about what is there now. Cases `RM-25`, `RM-26`.
- **Neither argument is refused, not raised.** A command that failed to parse must not strip anything,
  and the contract stays `(bool, str)` so nothing reaches a player as a traceback. Case `RM-31`.

The first implementation resolved the item string independently and then checked it was in the named
slot. For two rings sharing a key that returns the left one, which then fails the identity check
against `RIGHT_HAND` — refusing the exact call the argument exists to serve. `RM-29` is the only case
that sees it, and it was written before the code.

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
