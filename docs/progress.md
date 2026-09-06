# Progress

Running log of milestones with links to evidence. Reverse chronological — newest first.

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
