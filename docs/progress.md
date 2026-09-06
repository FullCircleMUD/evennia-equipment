# Progress

Running log of milestones with links to evidence. Reverse chronological — newest first.

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
