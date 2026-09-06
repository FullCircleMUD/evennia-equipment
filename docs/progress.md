# Progress

Running log of milestones with links to evidence. Reverse chronological — newest first.

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
