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
| `CR` | `EquipmentCarriableMixin` — an item's weight, and what may be stored in it |
| `CA` | `EquipmentCarryingMixin` — rebuilding a carrier's total weight from its contents |
| `PR` | `at_pre_object_receive` — refusing an object that cannot be carried |
| `RC` | `at_object_receive` — rebuilding when something arrives |
| `LV` | `at_object_leave` — rebuilding when something departs |
| `IN` | `at_init` — rebuilding when the carrier is loaded into memory |
| `TW` | The carried total, and the `extra_weight()` hook it calls |
| `CP` | Capacity, and the queries a consumer asks against it |
| `EW` | `effective_weight` — what an object contributes to whoever holds it |
| `WC` | `at_weight_changed` — a weight changing while the object is held |
| `CN` | `EquipmentContainerMixin` — an object that is both carried and carrying |

## Fixtures

The fake objects the suite needs, named and purposed. Typeclasses live in `tests/game_typeclasses.py`,
which imports nothing but the library.

| Fixture | Purpose |
|---|---|
| `CarriableThing` | A minimal typeclass carrying `EquipmentCarriableMixin` and declaring nothing of its own — the default-weight case |
| `HeavyThing` | A `CarriableThing` subclass overriding the weight default, mirroring a consumer's per-item defaults |
| `PaddedThing` | Contributes more than it weighs, standing in for how a container will behave |
| `NoisyThing` | Overrides `at_weight_changed()` and calls through, so both halves are observable |
| `Carrier` | A minimal typeclass carrying `EquipmentCarryingMixin` — the thing whose contents are summed |
| `BulkyCarrier` | A `Carrier` overriding the capacity default |
| `PurseCarrier` | A `Carrier` with `extra_weight()` and `extra_capacity()` overridden, both read from `ndb` so a test can change them mid-flight |
| `RecordingCarrier` | A `Carrier` with a witness mixin *below* it in the MRO — only reached if the library calls `super()` |
| `RefusingCarrier` | A `Carrier` whose chain vetoes every arrival, so the library must not overrule it |
| `Nowhere` | Carries no mixin: both somewhere to move an object to, and the object a carrier refuses |
| `Container` | A minimal typeclass carrying `EquipmentContainerMixin` — carried and carrying at once |
| `PanniersContainer` | A `Container` contributing only its own weight, as a mount's panniers would |

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

### CR — the carriable item

`EquipmentCarriableMixin` gives an item a weight and nothing else. It is the root of the library —
every other mixin sits downstream of it — so the type and range of this one value is worth pinning
precisely.

**Weight is a number, `int` or `float`, greater than or equal to zero**, coerced to `float` on the way
in so that one type always reads back out. The check lives in `at_set()`, per
[library-standards.md](../../../design/library-standards.md) § *Reading and writing object state*.

Booleans are refused explicitly, because `bool` subclasses `int` in Python: `isinstance(True, int)` is
`True`, so a plain numeric check accepts `True` and silently stores `1.0`.

| ID | Case | Test function |
|---|---|---|
| CR-01 | Weight defaults to `0.0` when nothing declares it | test_cr_01_weight_defaults_to_zero |
| CR-02 | A subclass can override the default weight | test_cr_02_a_subclass_can_override_the_default_weight |
| CR-03 | Two instances hold independent weights | test_cr_03_two_instances_hold_independent_weights |
| CR-04 | A float weight is stored as given | test_cr_04_a_float_weight_is_stored_as_given |
| CR-05 | An int weight is accepted and reads back as a float | test_cr_05_an_int_weight_reads_back_as_a_float |
| CR-06 | A weight of zero is accepted | test_cr_06_a_weight_of_zero_is_accepted |
| CR-07 | A negative weight is refused | test_cr_07_a_negative_weight_is_refused |
| CR-08 | A non-numeric weight is refused | test_cr_08_a_non_numeric_weight_is_refused |
| CR-09 | `None` is refused | test_cr_09_none_is_refused |
| CR-10 | A boolean weight is refused, `True` and `False` alike | test_cr_10_a_boolean_weight_is_refused |
| CR-11 | A weight set through `.db` bypasses validation and is stored unchecked | test_cr_11_a_weight_set_through_db_bypasses_validation |

`CR-11` pins a limit rather than a behaviour. `at_set()` fires only on assignment through the
descriptor, so a consumer writing `item.db.weight` stores whatever they like. The case exists so the
limit is stated rather than discovered, and so it is not later "fixed" by chasing the
`AttributeHandler` — which cannot be done from the library side.

### CA — rebuilding a carrier's weight

`_recalculate_item_weight()` rebuilds the carrier's item weight from scratch by summing what is in
`contents`. It is nuclear rather than incremental: every weight-changing event triggers a full rebuild,
so a missed event costs one stale reading rather than permanent drift. `obj.delete()` does not fire
`at_object_leave()` — confirmed in Evennia's `objects.py`, where the hook is called only from
`move_to()` — so that miss is real and the rebuild is what absorbs it.

**Every case here assumes no containers are present**, and none needed revising when they arrived: the
sum reads `effective_weight`, which a container answers for itself, so a container-free sum is still a
correct sum. The container's own cases are `CN`.

Only carriable objects reach `contents` — an object without `EquipmentCarriableMixin` is refused
entry, which is `at_pre_object_receive`'s job and gets its own cases with the hooks.

| ID | Case | Test function |
|---|---|---|
| CA-01 | Empty contents gives a weight of zero | test_ca_01_empty_contents_weighs_zero |
| CA-02 | One carriable object gives that object's weight | test_ca_02_one_object_gives_its_own_weight |
| CA-03 | Several carriable objects give their sum | test_ca_03_several_objects_give_their_sum |
| CA-04 | An excluded object is left out of the sum | test_ca_04_an_excluded_object_is_left_out |
| CA-05 | Recalculating twice gives the same answer | test_ca_05_recalculating_twice_gives_the_same_answer |
| CA-06 | A deleted object drops out on the next recalculation | test_ca_06_a_deleted_object_drops_out |

`CA-04` exists because Evennia fires `at_object_leave` *before* the object leaves `contents`, so the
rebuild has to be told to skip it. `CA-05` is what pins nuclear over incremental — two calls in a row
must not double the total. `CA-06` is the drift case that incremental tracking got wrong.

### PR — refusing what cannot be carried

`at_pre_object_receive` fires before the move and aborts it by returning `False`. An object without
`EquipmentCarriableMixin` has no weight, so it cannot take part in a weight system and is refused.

The refusal is logged, because an aborted move reports nothing to whoever attempted it — `move_to()`
returns `False` and the reason is lost. This is the log shim's first caller.

| ID | Case | Test function |
|---|---|---|
| PR-01 | An object without `EquipmentCarriableMixin` is refused | test_pr_01_an_object_without_the_mixin_is_refused |
| PR-02 | An object with the mixin is accepted | test_pr_02_an_object_with_the_mixin_is_accepted |
| PR-03 | A refusal from `super()` is passed on rather than overruled | test_pr_03_a_refusal_from_super_is_passed_on |
| PR-04 | A refused arrival is logged | test_pr_04_a_refused_arrival_is_logged |

`PR-03` is the one that breaks other libraries when it is missing: returning `True` unconditionally
overrules a veto from anything else in the chain, and nothing reports it.

### RC — rebuilding when something arrives

`at_object_receive` fires *after* the object is in `contents`, so the rebuild needs no `exclude`.

| ID | Case | Test function |
|---|---|---|
| RC-01 | An object moved in is counted, with no explicit rebuild | test_rc_01_an_object_moved_in_is_counted |
| RC-02 | An object created directly into the carrier is counted | test_rc_02_an_object_created_in_the_carrier_is_counted |
| RC-03 | `super()` is called | test_rc_03_receive_calls_super |

`RC-02` is a separate path — Evennia calls the hook itself when an object is created with a
`location`, which is how a game spawns something straight into an inventory.

### LV — rebuilding when something departs

`at_object_leave` fires *before* the object leaves `contents`, so the rebuild is given the departing
object as `exclude`. Without that it is still counted on the way out.

| ID | Case | Test function |
|---|---|---|
| LV-01 | An object moved out stops being counted | test_lv_01_an_object_moved_out_stops_being_counted |
| LV-02 | `super()` is called | test_lv_02_leave_calls_super |

### IN — rebuilding on load

`at_init` fires whenever Evennia loads the carrier into memory — server restart, cache eviction,
reload. Rebuilding there is what makes the total self-healing: drift that survived a shutdown is gone
the first time the object comes back.

| ID | Case | Test function |
|---|---|---|
| IN-01 | A stale total is corrected when the carrier is loaded | test_in_01_a_stale_total_is_corrected_on_load |
| IN-02 | An object not yet saved to the database does not raise | test_in_02_an_unsaved_carrier_does_not_raise |
| IN-03 | `super()` is called | test_in_03_init_calls_super |

`IN-02` guards `at_init` firing on a partially-constructed object, which raises during Django queryset
iteration otherwise.

### TW — the carried total

A carrier's total is its item weight plus whatever else the game counts as carried — coin, ore,
anything not modelled as an object. `extra_weight()` is the hook for that second part, defaulting to
zero, and the total is a property that adds the two.

The two are never merged into one calculation, because only one of them is visible to the library:
object movement fires Evennia hooks, a currency balance changing fires nothing. So item weight is
persisted and rebuilt on the events we see, and `extra_weight()` is called when the total is read,
needing no notification at all.

| ID | Case | Test function |
|---|---|---|
| TW-01 | `extra_weight()` returns zero by default | test_tw_01_extra_weight_defaults_to_zero |
| TW-02 | The total is item weight plus extra weight | test_tw_02_the_total_is_items_plus_extra |
| TW-03 | A consumer overriding `extra_weight()` changes the total | test_tw_03_overriding_extra_weight_changes_the_total |
| TW-04 | The total reflects a changed extra weight immediately, with nothing told to update | test_tw_04_the_total_reflects_a_changed_extra_weight_immediately |

`TW-04` is what pins compute-on-read. If the total were ever cached, a consumer's currency change
would need to notify the library, and that call would eventually be forgotten.

### CP — capacity

What a carrier can take, and the queries a consumer asks before letting it. The library answers the
questions; it does not decide what happens when the answer is no. Refusing the move, allowing it with
a penalty, or ignoring it entirely are all games' choices.

**Capacity mirrors weight.** A stored attribute holds what equipment and the game have set,
`extra_capacity()` is the hook for what is derived from state the library cannot see, and
`effective_capacity` adds them when read. So a strength potion needs nothing recalculated — nothing is
stored to go stale.

**The default is `float("inf")`**, which needs no new validation branch — infinity is a non-negative
float — and gives unlimited carrying without special-casing any of the queries. A library that instead
picked a number would be inventing a game's balance.

| ID | Case | Test function |
|---|---|---|
| CP-01 | Capacity is unlimited by default, so a huge load fits and does not encumber | test_cp_01_capacity_is_unlimited_by_default |
| CP-02 | Remaining capacity is infinite while capacity is unlimited | test_cp_02_remaining_capacity_is_infinite_by_default |
| CP-03 | A subclass can override the capacity default | test_cp_03_a_subclass_can_override_the_capacity_default |
| CP-04 | A negative capacity is refused | test_cp_04_a_negative_capacity_is_refused |
| CP-05 | `extra_capacity()` returns zero by default | test_cp_05_extra_capacity_defaults_to_zero |
| CP-06 | Effective capacity is the stored capacity plus extra capacity | test_cp_06_effective_capacity_is_stored_plus_extra |
| CP-07 | A consumer overriding `extra_capacity()` changes effective capacity | test_cp_07_overriding_extra_capacity_changes_the_effective_capacity |
| CP-08 | Remaining capacity is effective capacity less the total | test_cp_08_remaining_capacity_is_effective_less_the_total |
| CP-09 | Remaining capacity does not go below zero | test_cp_09_remaining_capacity_does_not_go_below_zero |
| CP-10 | `can_carry()` is true when the addition fits | test_cp_10_can_carry_is_true_when_it_fits |
| CP-11 | `can_carry()` is false when it does not | test_cp_11_can_carry_is_false_when_it_does_not |
| CP-12 | `is_encumbered` is false at exactly capacity | test_cp_12_is_encumbered_is_false_at_exactly_capacity |
| CP-13 | `is_encumbered` is true above capacity | test_cp_13_is_encumbered_is_true_above_capacity |

`CP-12` and `CP-13` are a pair on purpose: exactly-at-capacity is the boundary an off-by-one lands on.

### EW — what an object contributes

A carrier sums `effective_weight`, not `weight`. For a plain object the two are the same. For a
container they are not — it contributes its own weight plus what is inside it — so the container
answers for itself rather than the carrier learning what a container is.

That keeps `_recalculate_item_weight()` free of any container branch: the container arrives later as
an override of this one property and nothing in the carrier changes.

| ID | Case | Test function |
|---|---|---|
| EW-01 | An object's effective weight is its own weight | test_ew_01_effective_weight_is_the_objects_own_weight |
| EW-02 | The carrier's total is built from effective weight, not from `weight` | test_ew_02_the_total_is_built_from_effective_weight |

`EW-02` is what proves the seam: an object whose effective weight differs from its weight is counted
by the effective value, which is how a container will behave.

### WC — weight changing while held

The total rebuilds on arrival, departure and load. Without this it would not rebuild when an item
already held changes weight — enchanted lighter, a waterskin emptied — and the holder's total would
sit stale until something moved.

The notification is in the property's `__set__`, **not** in `at_set()`: `at_set()` runs before the
value is stored, so a rebuild triggered there would read the old weight back for this very object.

| ID | Case | Test function |
|---|---|---|
| WC-01 | Changing a held object's weight rebuilds the holder's total | test_wc_01_changing_a_held_objects_weight_rebuilds_the_total |
| WC-02 | Changing an unheld object's weight is harmless | test_wc_02_changing_an_unheld_objects_weight_is_harmless |
| WC-03 | An object held by something that does not carry is harmless | test_wc_03_an_object_held_by_a_non_carrier_is_harmless |
| WC-04 | A consumer's override still gets the rebuild by calling `super()` | test_wc_04_a_consumer_override_still_gets_the_rebuild |

Nesting is not covered here. An object inside a container notifies the container, and forwarding that
up to whoever holds the container arrives with `EquipmentContainerMixin`.

### CN — the container

A container is carried and carrying at once, so it takes both mixins. It adds two things: it
contributes its contents as well as itself, and it tells its own holder when that changes.

```python
class EquipmentContainerMixin(EquipmentCarriableMixin, EquipmentCarryingMixin):
```

The panniers case — a container whose contents do not count against whoever carries it — is a subclass
overriding `effective_weight`, not a flag. A flag would say there are exactly two modes; an override
also serves "half the weight", which a boolean cannot express.

| ID | Case | Test function |
|---|---|---|
| CN-01 | An empty container's effective weight is its own weight | test_cn_01_an_empty_containers_effective_weight_is_its_own |
| CN-02 | A loaded container's effective weight is its own weight plus its contents | test_cn_02_a_loaded_containers_effective_weight_includes_contents |
| CN-03 | A carrier counts a container's contents through it | test_cn_03_a_carrier_counts_a_containers_contents_through_it |
| CN-04 | Adding to a held container updates the carrier's total | test_cn_04_adding_to_a_held_container_updates_the_carrier |
| CN-05 | Removing from a held container updates the carrier's total | test_cn_05_removing_from_a_held_container_updates_the_carrier |
| CN-06 | Changing the weight of an item inside a held container updates the carrier's total | test_cn_06_changing_a_weight_inside_a_container_updates_the_carrier |
| CN-07 | Two levels of nesting propagate to the top | test_cn_07_two_levels_of_nesting_propagate_to_the_top |
| CN-08 | Propagation stops at a holder that does not carry | test_cn_08_propagation_stops_at_a_holder_that_does_not_carry |
| CN-09 | A container's own weight changing updates the carrier's total | test_cn_09_a_containers_own_weight_change_updates_the_carrier |
| CN-10 | A container refuses an object that cannot be carried | test_cn_10_a_container_refuses_what_cannot_be_carried |
| CN-12 | A container's extra weight counts toward what it contributes | test_cn_12_a_containers_extra_weight_counts_toward_what_it_contributes |
| CN-13 | A subclass may contribute only its own weight, excluding its contents | test_cn_13_a_subclass_may_contribute_only_its_own_weight |
| CN-14 | Loading a container into memory does not raise | test_cn_14_loading_a_container_into_memory_does_not_raise |

`CN-08` matters most: if the chain does not terminate the failure is a loop, not a wrong number. A
character is not carriable, and a room does not carry, so the walk upward runs out on its own.

`CN-10` is the composition check — inherited carrying behaviour still reachable through the MRO.

`CN-14` aims at a real risk. The container rebuilds on load and now notifies its holder, which reads
back into the container while Evennia is still constructing objects. `at_init` carries a `self.pk`
guard for that, and propagation reaches the rebuild by a route that does not pass through it.

`CN-11` was retired before it was written — a container's own capacity is inherited behaviour already
covered by `CN-10`.

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
