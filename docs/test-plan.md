# Test plan

Every test case the library commits to covering, and the test function that covers it. The library is
built test-first: cases are agreed here, tests are written against them, then the implementation is
written to pass. The **Test function** column is the auditable trail — it is filled in as each test is
written, so an empty cell means the case is agreed but not yet covered.

Case IDs are stable and referenceable. Do not renumber; retire an ID rather than reuse it. Every test
function carries its case ID as its docstring, so the trail reads in both directions.

All test functions live in `src/evennia_equipment/tests.py`.

Behaviour is agreed here first, before any test or code — see
[test-first-process.md](../../../design/test-first-process.md).

| Prefix | Covers |
|---|---|
| `SC` | The scaffold — the library is installed and the runner reaches it |

## Fixtures

The fake objects the suite needs, named and purposed.

| Fixture | Purpose |
|---|---|
| — | None yet. The scaffold cases need no fixtures; the table grows with the first behavioural surface |

## Cases

One section per function or surface, each with its own prefix and its own table.

### SC — the scaffold

Not behaviour of the library, but a check that there is a library to test. These fail when the editable
install is missing, when the test settings do not name the app, or when the runner cannot find the test
module — each of which otherwise looks like "no tests ran".

| ID | Case | Test function |
|---|---|---|
| SC-01 | The package is importable and carries its version | test_sc_01_the_package_is_importable_and_versioned |
| SC-02 | A log call outside an Evennia engine is a silent no-op rather than an error | test_sc_02_the_log_shim_is_a_no_op_outside_evennia |

## Open decisions

Surfaces this library is expected to grow, listed so they are not forgotten, and deliberately without
cases. A case here is a commitment, and nothing below has been designed yet.

- **[TBD — needs discussion: what a wearslot is.** How slots are named and enumerated, how a consumer
  declares a slot layout for a body shape that is not humanoid, and what happens when a layout changes
  under a character that is already wearing things.]
- **[TBD — needs discussion: inventory versus contents.** FCM keeps worn items in `contents` and
  distinguishes them by a flag, which makes "what I am carrying" and "what I hold" two different sets
  that read the same. Whether the library owns that distinction, and what it names the two, is open.]
- **[TBD — needs discussion: carrying capacity.** What contributes weight, what sets a capacity, and
  what being over it does — the last of which looks like consumer policy rather than library
  mechanism.]
- **[TBD — needs discussion: wear effects.** Whether an item modifying a wearer's stats while worn is
  this library's mechanism, a consumer concern, or something the library only signals.]
- **[TBD — needs discussion: what stays out.** Durability, fungible balances and item ownership are
  all adjacent to equipment in FCM and are not obviously this library's. Each needs a ruling before
  any of it is lifted.]
- **[TBD — needs discussion: settings and their defaults**, and which of them have no safe default and
  so are refused at boot.]
