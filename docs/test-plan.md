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
| `CF` | The slot enum a consumer declares, and the boot check that refuses a bad one |
| `WR` | `EquipmentWearableMixin` — an item's slot declaration, and what may be stored in it |
| `WS` | `EquipmentWearslotsMixin` — a wearer's slots, from the body plan its subclass declares |
| `WE` | `wear()` — choosing a group of slots and filling it |
| `RM` | `remove()` — freeing the slots an item occupies |
| `GW` | `get_all_worn()` — what a wearer has on |
| `GC` | `get_carried()` — what a wearer holds but is not wearing |
| `ID` | `wearslot_identity` — what an item is known by across a world rebuild |
| `ER` | `update_worn_equipment_record()` — writing down what is worn, to restore it later |
| `RW` | `restore_worn()` — putting the recorded equipment back on after a rebuild |
| `TG` | The filters this library publishes for `evennia-targeting` |
| `NS` | `contrib.utils.normalise_slot()` — one form to compare typed text and slot names in |
| `SM` | `contrib.utils.match_slot()` — turning what a player typed into a slot name |
| `CW` | `contrib.commands.CmdWear` — the command a player types |
| `CM` | `contrib.commands.CmdRemove` — the command a player types to take something off |

## Fixtures

The fake objects the suite needs, named and purposed, in two modules.

**`tests/game_typeclasses.py`** — real Evennia typeclasses carrying the library's mixins.
`AttributeProperty` needs an object with an attribute handler behind it, so the cases create these
rather than faking one. It imports Evennia, so tests import it inside a test body.

| Typeclass | Purpose |
|---|---|
| `CarriableThing` | Carries `EquipmentCarriableMixin` and declares nothing of its own — the default-weight case |
| `HeavyThing` | A `CarriableThing` overriding the weight default, mirroring a consumer's per-item defaults |
| `PaddedThing` | Contributes more than it weighs, so the sum is proved to read `effective_weight` rather than `weight` |
| `NoisyThing` | Overrides `at_weight_changed()` and calls through, so both halves are observable |
| `Carrier` | Carries `EquipmentCarryingMixin` — the thing whose contents are summed |
| `BulkyCarrier` | A `Carrier` overriding the capacity default |
| `PurseCarrier` | A `Carrier` with `extra_weight()` and `extra_capacity()` overridden, both read from `ndb` so a test can change them mid-flight |
| `RecordingCarrier` | A `Carrier` with `_RecordingHooks` *below* it in the MRO — reached only if the library calls `super()` |
| `RefusingCarrier` | A `Carrier` with `_RefusingHooks` below it, vetoing every arrival, so the library must not overrule it |
| `Container` | Carries `EquipmentContainerMixin` — carried and carrying at once |
| `PanniersContainer` | A `Container` contributing only its own weight, as a mount's panniers would |
| `PurseContainer` | A `Container` with `extra_weight()` overridden — coin inside a bag |
| `Nowhere` | Carries no mixin: both somewhere to move an object to, and the object a carrier refuses |
| `WearableThing` | Carries `EquipmentWearableMixin` and declares no slots — the undeclared case |
| `Helm` | A class-level slot declaration, so the check is proved to run on a default |
| `MistypedHelm` | A class-level declaration naming a slot the enum does not hold |
| `Helmet` | One group of one slot — the ordinary wearable |
| `Greatsword` | One group taking two slots at once |
| `Ring` | Two groups of one, so a second lands on the other hand |
| `Collar` | Declares a slot no humanoid has |
| `TwinRing` | A ring comparing equal to any other of its kind, as a consumer's typeclass may |
| `Humanoid` | A wearer with the humanoid body plan |
| `Dog` | A wearer with a different body plan, so `body_slots` is proved to be read |
| `Chimera` | Two slots where one name contains the other, so exact-match-wins is provable |
| `UnwearableHumanoid` | Refuses everything at `at_pre_wear()`, as a class or alignment rule would |
| `WatchfulHumanoid` | Records every post hook with its slots and what was worn at that moment |
| `UnwearableWatcher` | A `WatchfulHumanoid` refusing at `at_pre_wear()`, so a silent refusal is provable |
| `StuckWatcher` | A `WatchfulHumanoid` refusing at `at_pre_remove()` |

**`tests/slot_enums.py`** — the enums the `CF` cases point `EQUIPMENT_WEARSLOTS` at, standing in for a
consumer's own module. It **imports nothing but `enum`**: `check_settings()` resolves it during
`django.setup()`, while the app registry is still being built, so anything else it imported would be
pulled in at the worst possible moment.

| Value | What it is |
|---|---|
| `WearSlot` | Every slot any creature in the suite has. What it boots with |
| `NoMembers` | An enum declaring nothing — legal Python, useless as a slot list |
| `NonStringValue` | A member whose value is not a string, so it cannot key a slot dict |
| `RepeatedValue` | Two names, one value — Python folds the second into an alias |
| `NOT_AN_ENUM` | Not an enum at all, as a consumer gets by naming the wrong thing |

The `_slots()` helper in the suite swaps the setting and clears the resolved cache on the way in and
out. That simulates a restart with a different enum, which is the only way the slots ever change —
`valid_slot_names()` holds its answer for the life of the process.

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

### CF — the declared layouts

The slot names a game uses are content the library cannot invent, so they come from the consumer as a
setting naming an enum — see [library-standards.md](../../../design/library-standards.md) §
*Consumer-authored config*, and the same shape as `evennia-survival`'s stages.

```python
EQUIPMENT_WEARSLOTS = "world.wearslots.WearSlot"  # settings.py

class WearSlot(Enum):                              # world/wearslots.py
    HEAD = "HEAD"
    BODY = "BODY"
    LEFT_HAND = "LEFT_HAND"
    DOG_NECK = "DOG_NECK"
```

**One enum for every slot the game will ever have.** Which of them a given creature gets is a
subclass's business — see `WS`. This is the single list both sides are checked against: a wearer's
slots and an item's declaration.

No base class: a slot carries one thing, its name. Survival needs one because a stage carries three.

**A second required setting, `EQUIPMENT_IDENTITY_ATTRIBUTE`**, names the attribute an item carries as
its durable identity — a token id, an archive id, whatever survives a world rebuild. There is no name
the library could invent, so it has no default either.

```python
EQUIPMENT_IDENTITY_ATTRIBUTE = "token_id"
```

**Every problem is collected and raised together.** Two independent settings can both be wrong, and
stopping at the first turns that into fix-restart-fix-restart, once per mistake. A consumer gets the
whole list and works through it before trying again. Within the enum's own checks the sequence still
short-circuits, because each one makes the next meaningful.

**The bar is that nothing downstream crashes**, plus `CF-07`, which goes past it deliberately.

**What cannot be validated at boot is accepted rather than worked around.** Nothing at boot can see an
item, so an identity attribute naming something no item carries passes every check here and yields
`None` for every identity. The diagnostic is `restore_worn()` reporting how many it could not match.
The library validates what it can see, and says so.

| ID | Case | Test function |
|---|---|---|
| CF-01 | A missing `EQUIPMENT_WEARSLOTS` is refused at boot | test_cf_01_a_missing_setting_is_refused |
| CF-02 | A path that does not resolve is refused, with the original error chained | test_cf_02_an_unresolvable_path_is_refused_with_the_cause |
| CF-03 | Something that is not an `Enum` is refused | test_cf_03_something_that_is_not_an_enum_is_refused |
| CF-06 | An enum member whose value is not a string is refused | test_cf_06_a_non_string_member_value_is_refused |
| CF-07 | An enum with a repeated value is refused | test_cf_07_a_repeated_member_value_is_refused |
| CF-09 | A valid configuration boots | test_cf_09_a_valid_configuration_boots |
| CF-10 | The accessor returns the enum's values | test_cf_10_the_accessor_returns_the_enums_values |
| CF-11 | An enum with no members is refused | test_cf_11_an_enum_with_no_members_is_refused |
| CF-14 | A missing `EQUIPMENT_IDENTITY_ATTRIBUTE` is refused at boot | test_cf_14_a_missing_identity_attribute_is_refused |
| CF-15 | An identity attribute that is not a string is refused | test_cf_15_a_non_string_identity_attribute_is_refused |
| CF-16 | An empty identity attribute is refused | test_cf_16_an_empty_identity_attribute_is_refused |
| CF-17 | Both settings wrong are reported in one refusal, not the first only | test_cf_17_both_settings_wrong_are_reported_at_once |
| CF-18 | The accessor returns the declared attribute name | test_cf_18_the_accessor_returns_the_attribute_name |

Retired: `CF-04` (no mapping to be empty), `CF-05` (a plain string is caught by `CF-03`), `CF-08`
(superseded by `CF-17`, which collects across two settings rather than within one), `CF-12` and
`CF-13` (one accessor, covered by `CF-10`).

`CF-18` pins the accessor's shape. For a required setting the standards want a plain read — no
`getattr` fallback and no `if`, because boot has already guaranteed the value is there and usable.
Deferring the read is the only reason the accessor exists.

`CF-07` is the one worth having. Enum member *names* cannot repeat, but *values* can, and Python
silently makes the second an alias — `HEAD = "HEAD"` followed by `SKULL = "HEAD"` leaves one member
where the declaration reads as two. The check reads `__members__` rather than iterating the members,
because by the time you iterate, the duplicate has already been folded away.

`CF-06` exists because an enum's values are not necessarily strings. Slot names are dictionary keys
and are matched against item declarations, so `HEAD = 7` has to be refused rather than half-work.

`CF-11` refuses a named layout with no slots in it, which is a typo rather than a decision — a
creature that wears nothing does not carry the mixin. `CF-04` still accepts an empty *mapping*: a game
that has declared no body plans yet is mid-setup, not mistaken.


### WR — the item's slot declaration

An item declares which slots it occupies as a **list of groups**. Each group is one option, and every
slot inside a group is taken together:

```python
wearslot = [["HEAD"]]                            # a helm
wearslot = [["LEFT_FINGER"], ["RIGHT_FINGER"]]   # a ring — either finger
wearslot = [["WIELD", "HOLD"]]                   # a greatsword — both hands
wearslot = [["HEAD", "BODY", "LEGS"]]            # a suit of plate
```

**The canonical form is required, not normalised.** A flat list is genuinely ambiguous —
`["WIELD", "HOLD"]` could mean either hand or both — so converting one would be inventing a meaning
rather than tidying a shape. Refusing it says so at the point the mistake is made, and matches `CF-05`
refusing a bare-string layout rather than reading it letter by letter.

Two checks, both in `at_set()`. The format, and whether every name is in the declared slot enum. The
enum is as far as an item-side check can go — an item does not know which creature will wear it.
Whether *this* creature has the slots is `wear()`'s job.

| ID | Case | Test function |
|---|---|---|
| WR-01 | A canonical declaration is accepted | test_wr_01_a_canonical_declaration_is_accepted |
| WR-02 | A bare string is refused | test_wr_02_a_bare_string_is_refused |
| WR-03 | A flat list of names is refused | test_wr_03_a_flat_list_is_refused |
| WR-04 | A group holding a non-string is refused | test_wr_04_a_group_holding_a_non_string_is_refused |
| WR-05 | A declaration with no groups is refused | test_wr_05_a_declaration_with_no_groups_is_refused |
| WR-06 | A group with no slots is refused | test_wr_06_a_group_with_no_slots_is_refused |
| WR-07 | A slot name the enum does not hold is refused | test_wr_07_a_slot_the_enum_does_not_hold_is_refused |
| WR-08 | A slot name in the enum is accepted, whether or not any creature has it | test_wr_08_a_slot_in_the_enum_is_accepted |
| WR-09 | A class-level default is validated the first time it is read | test_wr_09_a_class_default_is_validated_on_first_read |
| WR-10 | A slot repeated inside one group is refused | test_wr_10_a_slot_repeated_in_one_group_is_refused |
| WR-11 | A declaration set through `.db` bypasses validation | test_wr_11_a_declaration_set_through_db_bypasses_validation |

`WR-08` is the scope of the name check: an item declaring `DOG_NECK` is valid even in a game whose
players are humanoid, because the item genuinely does not know its wearer. It is what would fail if
someone later "improved" the check to consult a particular wearer's slots.

`WR-09` matters because a typo in a typeclass would otherwise wait for someone to assign to it.
`AttributeProperty.__get__` autocreates by calling `__set__`, so the first read of any instance runs
the check.

`WR-10` refuses `[["HEAD", "HEAD"]]` — a group cannot take the same slot twice, and the repetition
would otherwise be folded silently, leaving a group that occupies less than it reads.

`WR-11` is the same documented limit as `CR-11`.

### WS — a wearer's slots

A consumer writes one subclass per body plan, naming the slots that creature has:

```python
class HumanoidEquipmentMixin(EquipmentWearslotsMixin):
    body_slots = (WearSlot.HEAD, WearSlot.BODY, WearSlot.LEFT_HAND, WearSlot.RIGHT_HAND)
```

`body_slots` is the declaration — enum members, so a typo is an `AttributeError` where it is written.
`worn_items` is the storage: a real, persisted dictionary of slot name to the item in it or `None`,
built once and mutated from then on. `wear()` assigns an item, `remove()` assigns `None`.

**`at_init()` reconciles the two**, once per load rather than on every read. It builds the dictionary
when there isn't one, adds slots the class has gained and drops slots it has lost. When the declared
names already match the dictionary's keys it returns without writing, which is every load but the
first after a code change.

An item in a dropped slot simply stops being worn. Nothing moves — a worn item never left `contents`,
so it is already in inventory.

| ID | Case | Test function |
|---|---|---|
| WS-01 | A wearer's slots come from its `body_slots` | test_ws_01_slots_come_from_body_slots |
| WS-02 | Every slot starts empty | test_ws_02_every_slot_starts_empty |
| WS-03 | Slots keep the order `body_slots` declares them in | test_ws_03_slots_keep_the_declared_order |
| WS-04 | Two wearers with different `body_slots` have different slots | test_ws_04_different_body_slots_give_different_slots |
| WS-11 | An absent or empty dictionary is populated on load | test_ws_11_an_empty_dictionary_is_populated_on_load |
| WS-12 | A slot added to `body_slots` is added on load | test_ws_12_a_slot_added_to_body_slots_is_added_on_load |
| WS-13 | A slot removed from `body_slots` is removed on load | test_ws_13_a_slot_removed_from_body_slots_is_removed_on_load |
| WS-14 | An item in a removed slot stops being worn and stays carried | test_ws_14_an_item_in_a_removed_slot_stops_being_worn |
| WS-15 | A subclass declaring a slot the enum does not hold is refused at import | test_ws_15_a_slot_the_enum_does_not_hold_is_refused_at_import |
| WS-16 | Reconciliation leaves existing assignments in place | test_ws_16_reconciliation_leaves_existing_assignments_alone |
| WS-17 | A subclass declaring no slots is refused at import | test_ws_17_a_subclass_declaring_no_slots_is_refused |
| WS-18 | A subclass declaring a plain string instead of an enum member is refused | test_ws_18_a_plain_string_instead_of_an_enum_member_is_refused |
| WS-19 | A subclass repeating a slot is refused | test_ws_19_a_repeated_slot_is_refused |

Every import-time refusal names the class, the slot at fault and what to do about it. A consumer
meeting one has written a typeclass, not called an API, so the message has to be readable where it
lands — in a traceback during startup, with no context but itself.

Retired: `WS-05` through `WS-10`. There is no layout key to be wrong, and the earlier reconciliation
design ran on every read rather than once per load.

`WS-03` matters because the display reads in declaration order — head to toe rather than alphabetical.

`WS-11` is what covers an object that predates the mixin. `at_object_creation` fires once and has
already run for such an object, so it would never get a dictionary; `at_init` fires on every load.

`WS-15` fires at class-definition time, via `__init_subclass__`. Nothing at boot can enumerate a
consumer's typeclasses, so the moment their module is imported is the earliest the library can see one.
It is the mirror of `WR-07` — both sides checked against the same enum, so a typo on either is
reported where it was written.

`WS-16` is the one that costs a player their gear if it is wrong. Adding a slot must add a key, not
rebuild the dictionary — a rebuild would pass `WS-12` and quietly strip everything the character had
on.

`WS-18` exists because the failure without it is obscure: `body_slots = ("HEAD",)` dies on `s.value`
deep inside the mixin, naming neither the class nor the line that wrote it.

### WE — wearing

`wear(item)` takes **a string or an object** and returns `(bool, message)`.

**Both, because the redundancy is otherwise unavoidable.** A command handed only objects has to filter
the wearer's contents to find one, and then `wear()` filters again to confirm what the caller just
established. Resolving inside means the work happens once. An object is still accepted, because
`restore_worn()` and a consumer equipping something it has just created both hold one already — and two
identical rings are distinct objects but the same string.

**Resolution is a filter, not a search.** The candidates come from `walk_contents` with
`f_key_matches`, so the name test lives beside every other filter in the ecosystem rather than inside
this one function.

The order is what makes the refusals accurate:

1. Match against what is carried and not worn. One or more results, that is the answer.
2. Otherwise match against what is worn — a hit there means "you are already wearing it", which is a
   different answer to "you are not carrying it".
3. Otherwise nothing matched.

**Several matches are two different situations.** Items sharing a key are interchangeable, so the
first is worn and the player is not asked a question with no useful answer. Items with different keys
are a genuine question, and the reply echoes what was typed — `Which ring do you mean?` — rather than
listing the candidates, which could be five.

Selection then walks the item's groups in declaration order and takes the first one where **every**
slot exists on this wearer and is free. Group order is therefore the item author's preference —
`[["RIGHT_FINGER"], ["LEFT_FINGER"]]` favours the right hand — and the library holds no opinion about
it.

**`slot=` overrides that preference.** Naming a slot narrows the candidate groups to those *containing*
it, and selection proceeds as before over what is left. Without it, nothing changes.

Group order alone cannot express "not the obvious one". A shortsword declaring
`[["WIELD"], ["HOLD"]]` goes to the wield hand whenever that hand is free, so a player asking to hold
it gets it wielded — and a ring is always put on the first free finger, never the one asked for. The
argument is what lets a command mean a particular place.

**A slot is named as an enum member or as its value.** `body_slots` is declared with members and
`worn_items` is keyed by their values, so a consumer holds one and the library holds the other. Taking
both costs a line and removes a trap that would otherwise bite once per consumer.

Two refusals, kept apart because the player's fix differs: an item that cannot go there at all, and a
wearer that has no such place.

| ID | Case | Test function |
|---|---|---|
| WE-01 | A single-slot item fills that slot | test_we_01_a_single_slot_item_fills_that_slot |
| WE-02 | A multi-slot item fills every slot in its group | test_we_02_a_multi_slot_item_fills_every_slot_in_its_group |
| WE-03 | The first group with all its slots free is chosen | test_we_03_the_first_free_group_is_chosen |
| WE-04 | A later group is chosen when an earlier one is occupied | test_we_04_a_later_group_is_chosen_when_the_first_is_taken |
| WE-05 | A partly-blocked group is skipped rather than partly filled | test_we_05_a_partly_blocked_group_is_not_partly_filled |
| WE-06 | A group naming a slot this wearer does not have is skipped | test_we_06_a_group_naming_a_missing_slot_is_skipped |
| WE-07 | An item not in contents is refused | test_we_07_an_item_not_in_contents_is_refused |
| WE-08 | An item already worn is refused | test_we_08_an_item_already_worn_is_refused |
| WE-09 | An item declaring no slots is refused | test_we_09_an_item_declaring_no_slots_is_refused |
| WE-10 | Wearing is refused when no group is usable | test_we_10_wearing_is_refused_when_no_group_is_usable |
| WE-11 | Wearing does not move the item out of contents | test_we_11_wearing_does_not_move_the_item |
| WE-12 | Wearing does not change the carried weight | test_we_12_wearing_does_not_change_the_carried_weight |
| WE-13 | Both outcomes return a message | test_we_13_both_outcomes_return_a_message |
| WE-14 | A string naming a carried item wears it | test_we_14_a_string_naming_a_carried_item_wears_it |
| WE-15 | Matching ignores case | test_we_15_matching_ignores_case |
| WE-16 | A string matching part of a key matches that item | test_we_16_a_substring_of_the_key_matches |
| WE-17 | A string matching nothing is refused as not carried | test_we_17_a_string_matching_nothing_is_refused_as_not_carried |
| WE-18 | A string matching only a worn item is refused as already worn | test_we_18_a_string_matching_only_a_worn_item_says_already_worn |
| WE-19 | Of several matches sharing a key, the first is worn | test_we_19_of_several_matches_sharing_a_key_the_first_is_worn |
| WE-20 | Matches with differing keys are refused with the word that was typed | test_we_20_matches_with_differing_keys_are_refused_with_the_typed_word |
| WE-21 | A carried item wins over a worn one matching the same string | test_we_21_a_carried_item_wins_over_a_worn_one |
| WE-22 | An object is worn without being resolved | test_we_22_an_object_is_worn_without_being_resolved |
| WE-23 | A named slot is chosen over an earlier free group | test_we_23_a_named_slot_is_chosen_over_an_earlier_free_group |
| WE-24 | Naming one slot of a multi-slot group fills the whole group | test_we_24_naming_one_slot_of_a_group_fills_the_whole_group |
| WE-25 | A named slot the item does not declare is refused | test_we_25_a_named_slot_the_item_does_not_declare_is_refused |
| WE-26 | A named slot this wearer does not have is refused | test_we_26_a_named_slot_this_wearer_does_not_have_is_refused |
| WE-27 | A named slot that is already occupied is refused | test_we_27_a_named_slot_already_occupied_is_refused |
| WE-28 | A slot named as an enum member works as its value does | test_we_28_a_slot_named_as_an_enum_member_works |
| WE-29 | A slot can be named while the item is given as a string | test_we_29_a_slot_can_be_named_while_the_item_is_a_string |
| WE-30 | `at_pre_wear()` allows wearing by default | test_we_30_at_pre_wear_allows_by_default |
| WE-31 | A consumer refusing stops the wearing and fills no slot | test_we_31_a_consumer_refusing_stops_the_wearing |
| WE-32 | The consumer's reason is what `wear()` returns | test_we_32_the_consumers_reason_is_returned |
| WE-33 | `at_post_wear()` sees the slots already filled | test_we_33_at_post_wear_sees_the_slots_already_filled |
| WE-34 | `at_post_wear()` receives the slots that were filled | test_we_34_at_post_wear_receives_the_slots_filled |
| WE-35 | `at_post_wear()` does not fire when wearing is refused | test_we_35_at_post_wear_does_not_fire_when_refused |
| WE-36 | `restore_worn()` fires `at_post_wear()` for each item put back | test_we_36_restore_worn_fires_at_post_wear |

`WE-05` is the one that bites if the implementation fills slots as it checks them: a group that turns
out to be blocked half-way through would leave the wearer holding an item in some of its slots and
not others. Selection has to complete before anything is written.

`WE-12` ties back to the carrying half. Wearing moves a reference, not an object, so the total must
not shift — which is why the two mixins compose without either knowing about the other.

`WE-13` pins the contract the command layer depends on: the mixin answers, the command speaks.

`WE-18` is the case a single-pass implementation gets wrong. Matching only the unworn items and
stopping there tells a player wearing the helmet that they are not carrying it, which is both false and
useless. It is the reason resolution is two ordered passes rather than one filter.

`WE-21` is the same ordering seen from the other side, and the reason the passes are ordered rather
than merged. A player wearing one iron ring and carrying another means `wear ring` while dressed; the
carried one is the only one that can be worn, and a merged pass could return either.

`WE-19` and `WE-20` are the two halves of "several matched". Interchangeable items are an answer, not a
question — asking which of two identical rings is wanted has no answer a player can give. Differently
named ones are a real question, and `WE-20` pins that the reply quotes what was typed rather than
listing candidates.

`WE-22` keeps the object path intact. `restore_worn()` and a consumer equipping a freshly created item
both hold the object already, and resolving by key would be ambiguous exactly where objects are not.

`WE-23` is the case the argument exists for, and the one an implementation that merely *checks* the
named slot would pass by accident. A ring with both fingers free must go on the one that was asked for,
not the one declared first.

`WE-24` fixes what naming a slot means: the group containing it, not the slot alone. A greatsword
named by one hand still takes both, because a group is taken together or not at all — the same rule
`WE-05` pins for the unnamed case.

`WE-25` and `WE-26` are separate because the answers are. "That cannot go there" is about the item;
"you have no such place" is about the wearer, and it is what a player naming a slot the game does not
give them needs to hear. One message for both would be wrong half the time.

`WE-28` is a trap that would otherwise bite once per consumer. A game declares `body_slots` with enum
members and reads `worn_items` keyed by their values, so whichever the library demanded would be the
other one to somebody.

**The four hooks.** `at_pre_wear(item)` and `at_pre_remove(item)` return `(bool, str)` and can refuse;
`at_post_wear(item, slots)` and `at_post_remove(item, slots)` return nothing and fire only on success.
The library refuses nothing of its own in any of them.

They exist because equipment changes a character. A ring of strength is worth nothing until something
recalculates the wearer's strength, and that has to happen on both edges — the library has no idea what
a consumer's stats are, and a consumer has no other moment to learn that the set of worn items changed.

`WE-33` is the ordering that makes them usable: the slots are already written when `at_post_wear` runs,
so a consumer recalculating from `get_all_worn()` sees the item it was told about. Firing before the
write would give a hook that has to be told the answer twice.

`WE-34` is why the slots are passed. A consumer can read `worn_items` at post-wear, but `RM-33`'s
mirror cannot — by then the slots are freed and where the item *was* exists nowhere else. Passing them
on both sides keeps the pair symmetrical rather than making one of them the exception.

`WE-36` is the case that matters after a shard move. Restoring rebuilds the worn set through `wear()`,
so the bonuses come back with it — a restore that put the items on without firing the hooks would leave
a character wearing a ring of strength and no stronger for it.

### RM — removing

`remove(item)` frees every slot the item occupies and leaves it in `contents`. Taking something off
does not put it down.

**It takes a string or an object**, on the same reasoning as `wear()` and with the search mirrored: a
string resolves against what the wearer has on, not what it carries. A command that had to find the
object first would filter the worn items to get one, and then `remove()` would ask the slot map again
to confirm what the caller had just established.

The passes are ordered the same way, and the second one is what makes the refusal useful:

1. Match against what is worn. One or more results, that is the answer.
2. Otherwise match against what is carried — a hit there means "you are not wearing that", which is a
   better answer than "you have no such thing".
3. Otherwise nothing matched.

Several matches split the same way: items sharing a key are interchangeable, so the first comes off;
differing keys are a question, and the reply echoes what was typed.

**`slot=` names where to take it from**, and unlike `wear()` it can stand on its own — `remove(None,
slot=...)` takes off whatever is in that slot. Wearing nothing into a slot means nothing, so `wear()`
keeps its item required; taking off "whatever is on my right finger" is a complete instruction.

| Call | Means |
|---|---|
| `remove("ring")` | the worn items matching, first if they share a key |
| `remove("ring", slot="RIGHT_FINGER")` | that item, and only if it is in that slot |
| `remove(None, slot="RIGHT_FINGER")` | whatever is in that slot |
| `remove()` | neither — a caller bug, refused rather than guessed at |

**Two identical rings is what it is for.** `Which one do you mean?` cannot help when both keys are the
same, so naming the slot is the only way a player can say which hand. Nothing else on the surface
solves it.

It is `slot`, not `location`: `location` is Evennia's word for where an object *is*, and a worn ring's
location is the wearer.

`at_pre_remove(item)` is the one gate, returning `(bool, str)` — the same shape `remove()` returns, so
a consumer's reason reaches the player rather than being replaced by something generic. It allows by
default, and the library refuses nothing of its own.

**On the wearer rather than the item**, deliberately. A cursed item is the item's business, but "you
are paralysed" or "not in combat" is the wearer's, and an item-side hook cannot express those. A
consumer wanting item-side logic delegates to the item in one line; the reverse is not available.

| ID | Case | Test function |
|---|---|---|
| RM-01 | Removing frees the slot | test_rm_01_removing_frees_the_slot |
| RM-02 | Removing a multi-slot item frees every slot it occupied | test_rm_02_removing_frees_every_slot_it_occupied |
| RM-03 | Removing an item that is not worn is refused | test_rm_03_removing_something_not_worn_is_refused |
| RM-04 | Removing leaves the item in contents | test_rm_04_removing_leaves_the_item_in_contents |
| RM-05 | Removing does not change the carried weight | test_rm_05_removing_does_not_change_the_carried_weight |
| RM-06 | Other worn items are unaffected | test_rm_06_other_worn_items_are_unaffected |
| RM-07 | A removed item can be worn again | test_rm_07_a_removed_item_can_be_worn_again |
| RM-08 | Both outcomes return a message | test_rm_08_both_outcomes_return_a_message |
| RM-09 | Removing one of two identical items frees only that one | test_rm_09_removing_one_of_two_identical_items_frees_only_that_one |
| RM-10 | `at_pre_remove()` allows removal by default | test_rm_10_the_hook_allows_removal_by_default |
| RM-11 | A consumer refusing stops the removal and the item stays worn | test_rm_11_a_consumer_refusing_stops_the_removal |
| RM-12 | The consumer's reason is what `remove()` returns | test_rm_12_the_consumers_reason_is_returned |
| RM-13 | The slots are untouched when removal is refused | test_rm_13_the_slots_are_untouched_when_removal_is_refused |
| RM-14 | A string naming a worn item removes it | test_rm_14_a_string_naming_a_worn_item_removes_it |
| RM-15 | Matching ignores case | test_rm_15_matching_ignores_case |
| RM-16 | A string matching part of a key matches that item | test_rm_16_a_substring_of_the_key_matches |
| RM-17 | A string matching nothing is refused | test_rm_17_a_string_matching_nothing_is_refused |
| RM-18 | A string matching only a carried item is refused as not worn | test_rm_18_a_string_matching_only_a_carried_item_says_not_worn |
| RM-19 | Of several matches sharing a key, the first is removed | test_rm_19_of_several_matches_sharing_a_key_the_first_is_removed |
| RM-20 | Matches with differing keys are refused with the word that was typed | test_rm_20_matches_with_differing_keys_are_refused_with_the_typed_word |
| RM-21 | A worn item wins over a carried one matching the same string | test_rm_21_a_worn_item_wins_over_a_carried_one |
| RM-22 | An object is removed without being resolved | test_rm_22_an_object_is_removed_without_being_resolved |
| RM-23 | A named slot alone removes whatever is in it | test_rm_23_a_named_slot_alone_removes_what_is_in_it |
| RM-24 | Naming one slot of a multi-slot item frees every slot it occupied | test_rm_24_naming_one_slot_frees_every_slot_it_occupied |
| RM-25 | A named slot this wearer does not have is refused | test_rm_25_a_named_slot_this_wearer_does_not_have_is_refused |
| RM-26 | A named slot holding nothing is refused | test_rm_26_a_named_slot_holding_nothing_is_refused |
| RM-27 | An item and a slot together remove that item from that slot | test_rm_27_an_item_and_a_slot_remove_that_item_from_that_slot |
| RM-28 | An item worn somewhere other than the named slot is refused | test_rm_28_an_item_worn_elsewhere_than_the_named_slot_is_refused |
| RM-29 | Of two items sharing a key, the one in the named slot is removed | test_rm_29_of_two_items_sharing_a_key_the_one_in_the_slot_is_removed |
| RM-30 | A slot named as an enum member works as its value does | test_rm_30_a_slot_named_as_an_enum_member_works |
| RM-31 | Neither an item nor a slot is refused | test_rm_31_neither_an_item_nor_a_slot_is_refused |
| RM-32 | `at_post_remove()` sees the slots already freed | test_rm_32_at_post_remove_sees_the_slots_already_freed |
| RM-33 | `at_post_remove()` receives the slots that were freed | test_rm_33_at_post_remove_receives_the_slots_freed |
| RM-34 | `at_post_remove()` does not fire when removal is refused | test_rm_34_at_post_remove_does_not_fire_when_refused |

`RM-02` is the counterpart to `WE-02`: a two-handed item sits under two keys, and freeing only the
first leaves a phantom holding the other hand for good.

`RM-06` catches the lazy implementation — clearing the whole stored dict passes `RM-01` and `RM-02`
while quietly stripping everything else the wearer had on.

`RM-07` is the round trip. An item whose slots are freed but which is still referenced somewhere else
reads as worn, so `wear()` refuses it — a failure neither `RM-01` nor `WE-08` sees on its own.

`RM-13` is the counterpart to `WE-05`: a refusal must leave the slots exactly as they were, not
half-freed.

`RM-09` is about identity rather than equality. A consumer's typeclass may define `__eq__` — by key,
or by a token id — and comparing slots with `==` would then clear every slot holding an item that
merely *compares* equal. The library asks "is this the object in that slot", so the comparison is
`is`, and this is the case that says so.

`RM-18` is `WE-18` seen from the other side, and the one a single-pass implementation gets wrong.
Searching only the worn items tells a player holding the boots that no such thing exists, when the
useful answer is that they are carrying them and not wearing them.

`RM-21` is the ordering that `RM-18` implies. Wearing one iron ring and carrying another, `remove ring`
has exactly one sensible target, and a merged pass could return either.

`RM-19` and `RM-20` are the two halves of "several matched", as `WE-19` and `WE-20` are for wearing.
Asking which of two identical rings is meant has no answer a player can give; two differently named
items do.

`RM-22` keeps the object path intact. A consumer stripping a specific item — a curse breaking, a
scripted disarm — holds the object already, and resolving by key would be ambiguous exactly where
objects are not.

`RM-29` is the case the argument exists for, and the one nothing else on the surface can reach. Two
rings with the same key, one on each hand: `remove ring` takes the first, and asking "which ring?"
would have no answer a player could give. The slot is the only way to say which hand.

`RM-24` mirrors `WE-24`. A slot names the item occupying it, and removing that item frees everywhere it
sits — a greatsword named by one hand does not come half off.

`RM-25` and `RM-26` are separate for the same reason `WE-25` and `WE-26` are. "You have no right
finger" is about the wearer's body; "you are wearing nothing on your right finger" is about what is
there now, and only the second invites the player to look again.

`RM-31` is a caller bug rather than a player one — a command that failed to parse. It is refused rather
than raised, so the contract stays `(bool, str)` and nothing reaches a player as a traceback.

`RM-33` is the reason the post hooks are given slots at all. At post-wear a consumer could read
`worn_items` instead; at post-remove it cannot, because the slots are freed by then and where the item
sat exists nowhere else. See the hook notes under `WE`.

`RM-34` is the pairing `WE-35` makes on the other side. A refused removal must leave a consumer's stats
alone, and a post hook that fired anyway would strip a ring's bonus from a character still wearing it.

### GW — what is worn

`get_all_worn()` returns the items a wearer has on, each once however many slots it fills.

**Built from `contents`, not from the slot map.** The slot map can hold an object that no longer
exists — `delete()` fires no hook, so nothing clears it — and an answer assembled from `contents`
cannot return a ghost. The same reasoning that made the weight total a rebuild rather than a running
figure.

| ID | Case | Test function |
|---|---|---|
| GW-01 | Nothing worn gives an empty result | test_gw_01_nothing_worn_gives_an_empty_result |
| GW-02 | A worn item is listed | test_gw_02_a_worn_item_is_listed |
| GW-03 | A multi-slot item is listed once, not once per slot | test_gw_03_a_multi_slot_item_is_listed_once |
| GW-04 | A carried but unworn item is not listed | test_gw_04_a_carried_item_is_not_listed |
| GW-05 | A deleted item is no longer listed | test_gw_05_a_deleted_item_drops_out |
| GW-06 | Of two items that compare equal, only the worn one is listed | test_gw_06_of_two_equal_items_only_the_worn_one_is_listed |

### GC — what is carried

`get_carried()` returns what is in `contents` and not worn — what a player means by "my inventory",
as against everything the object holds.

| ID | Case | Test function |
|---|---|---|
| GC-01 | Empty contents gives an empty result | test_gc_01_empty_contents_gives_an_empty_result |
| GC-02 | A carried item is listed | test_gc_02_a_carried_item_is_listed |
| GC-03 | A worn item is not listed | test_gc_03_a_worn_item_is_not_listed |
| GC-04 | A multi-slot worn item is not listed | test_gc_04_a_multi_slot_worn_item_is_not_listed |
| GC-05 | Worn and carried together account for everything in contents | test_gc_05_worn_and_carried_account_for_all_contents |
| GC-06 | Of two items that compare equal, the unworn one is listed | test_gc_06_of_two_equal_items_the_unworn_one_is_listed |

`GC-05` is the invariant that matters: the two are a partition, so nothing in `contents` can fall
through both and become invisible to a player.

`GC-04` guards the implementation that asks "is this in the first slot it declared" rather than "is
this worn at all" — a greatsword would then show up in the inventory listing as well as both hands.

`GW-06` and `GC-06` are the two halves of one failure. Both lists are built by asking whether an
object is among the worn ones, and a set membership test uses `__hash__` and `__eq__` — which a
consumer's typeclass may define by key or by token id. Two rings that compare equal, one worn, would
then both read as worn: the carried one disappearing from the player's inventory and the worn one
appearing twice. The comparison is by identity for that reason.

### ID — what an item is known by

A world rebuild reissues every primary key, so a database reference cannot survive it. What can is
whatever the game already uses to identify an item permanently — a token id, an archive id — named
once in `EQUIPMENT_IDENTITY_ATTRIBUTE` and read off the item as `wearslot_identity`.

| ID | Case | Test function |
|---|---|---|
| ID-01 | The identity is read from the attribute `EQUIPMENT_IDENTITY_ATTRIBUTE` names | test_id_01_the_identity_is_read_from_the_named_attribute |
| ID-02 | An item without that attribute has no identity | test_id_02_an_item_without_the_attribute_has_no_identity |
| ID-03 | A consumer overriding the accessor wins | test_id_03_a_consumer_overriding_the_accessor_wins |

`ID-02` is not a failure. An item with no identity is worn perfectly well; it simply cannot be
restored, because there is nothing to match it by. Inventing a key would be worse — restore would
look for something that never existed.

`ID-03` is for a game whose items are not uniform. The setting covers the common case; a typeclass
that keeps its identity somewhere else overrides the accessor instead.

### ER — writing down what is worn

`update_worn_equipment_record()` rebuilds `worn_equipment_record` from what the wearer currently has
on. A consumer calls it before archiving — FCM wires it into its own archive path, so there is one
call site rather than scattered ones.

**The record is persisted, not held in memory.** It has to survive the very event that destroys
everything else about the wearer's equipment, so it is an attribute on the object and never `ndb`.

**It is rebuilt, not appended to.** The record describes what is worn now, so anything taken off since
the last call is absent from it.

| ID | Case | Test function |
|---|---|---|
| ER-01 | Nothing worn gives an empty record | test_er_01_nothing_worn_gives_an_empty_record |
| ER-02 | A worn item's identity is recorded | test_er_02_a_worn_items_identity_is_recorded |
| ER-03 | A carried but unworn item is not recorded | test_er_03_a_carried_item_is_not_recorded |
| ER-04 | An item with no identity is skipped | test_er_04_an_item_with_no_identity_is_skipped |
| ER-05 | An item taken off since the last call is no longer in the record | test_er_05_an_item_taken_off_is_no_longer_in_the_record |
| ER-06 | Calling it twice gives the same result | test_er_06_calling_it_twice_gives_the_same_result |
| ER-07 | The record is persisted on the wearer, not held in memory | test_er_07_the_record_is_persisted_not_held_in_memory |

`ER-05` is what makes it a record of the present rather than a history. An append-only implementation
passes every other case here and slowly accumulates gear the character no longer owns, which restore
would then look for and never find.

`ER-07` is the case the word "cache" would have talked us out of. A record that does not survive the
archive is worth nothing, since surviving the archive is the only reason it exists.

### RW — putting the equipment back on

`restore_worn()` walks `contents` and wears anything whose identity is in the record. A consumer calls
it after their own restore has put the items back — the library has no way to know when that is.

**It walks `contents`, not the record.** An identity matching nothing is then never visited, so there
is nothing to ignore explicitly and no case for it. Every outcome is a `(bool, str)` from `wear()`
itself, so the library grows no second vocabulary for the same refusals.

**Order does not matter.** The items all fitted simultaneously when the record was written, so they
all fit now, whatever order `contents` gives them. No sorting, no second pass, no rollback.

| ID | Case | Test function |
|---|---|---|
| RW-01 | An item whose identity is in the record is worn | test_rw_01_an_item_in_the_record_is_worn |
| RW-02 | An item not named in the record stays carried | test_rw_02_an_item_not_in_the_record_stays_carried |
| RW-03 | An item already worn returns `wear()`'s refusal | test_rw_03_an_item_already_worn_returns_wears_refusal |
| RW-04 | An item that cannot be worn returns `wear()`'s refusal | test_rw_04_an_item_that_cannot_be_worn_returns_wears_refusal |
| RW-05 | The record is unchanged by restoring | test_rw_05_the_record_is_unchanged_by_restoring |
| RW-06 | An item that is not wearable at all is passed over | test_rw_06_an_item_that_is_not_wearable_is_passed_over |

`RW-04`'s real trigger is a slot removed from `body_slots` since the record was written. The item comes
back carried rather than worn, and the refusal says why — which is the whole diagnostic a consumer
gets.

`RW-03` means calling it twice reports every item as a failure the second time. That is correct for
one call per restore, which is the intended use, and worth knowing rather than discovering: under
`evennia-scaling` this runs on every shard move.

`RW-06` is the ordinary case that walking `contents` invites. A character carries rocks and bread as
well as armour, and a plain carriable item has no `wearslot_identity` to ask about — reading one
raises rather than returning `None`.

A returned list of refusals is also the only signal that `EQUIPMENT_IDENTITY_ATTRIBUTE` names
something the game's items do not carry — every identity is then `None`, the record is empty, and
nothing is restored.

### TG — the filters this library publishes

Two factories in `src/evennia_equipment/targeting.py`, the module every library extending
`evennia-targeting` puts its own filters in. They are what the library's own walks over `contents` are
built from, and they are published so a consumer filtering by the same thing uses this definition
rather than writing a second one.

**Factories, not predicates.** Both close over data assembled once — the occupied slots, the record —
rather than recomputing it for every object the walk visits.

| ID | Case | Test function |
|---|---|---|
| TG-01 | `f_worn_by` passes the library's own factory validator | test_tg_01_f_worn_by_passes_the_factory_validator |
| TG-02 | A worn item passes the filter | test_tg_02_a_worn_item_passes |
| TG-03 | A carried but unworn item does not | test_tg_03_a_carried_item_does_not |
| TG-04 | An item filling several slots passes | test_tg_04_a_multi_slot_item_passes |
| TG-05 | Of two items that compare equal, only the worn one passes | test_tg_05_of_two_equal_items_only_the_worn_one_passes |
| TG-06 | A wearer with nothing on matches nothing | test_tg_06_a_wearer_with_nothing_on_matches_nothing |
| TG-07 | The occupied slots are read once, when the filter is built | test_tg_07_the_occupied_slots_are_read_once_at_build_time |
| TG-08 | `f_identity_in` passes the library's own factory validator | test_tg_08_f_identity_in_passes_the_factory_validator |
| TG-09 | An item whose identity is in the set passes | test_tg_09_an_item_whose_identity_is_in_the_set_passes |
| TG-10 | An item whose identity is not in the set does not | test_tg_10_an_item_whose_identity_is_not_in_the_set_does_not |
| TG-11 | An item carrying no identity attribute is passed over rather than raising | test_tg_11_an_item_with_no_identity_attribute_is_passed_over |
| TG-12 | An empty set matches nothing rather than raising | test_tg_12_an_empty_set_matches_nothing_rather_than_raising |

`TG-01` and `TG-08` call `validate_factory` from `evennia_targeting.testing`, which checks the call
shape, the prefix, a real `bool` return and determinism. It is the sibling's own contract, applied to
our filters by the sibling's own code — a hand-written equivalent would drift from it.

`TG-05` is the identity guarantee that `GW-06` and `GC-06` pin at the surface, pinned here at the
filter. A set membership test uses `__hash__` and `__eq__`, either of which a consumer's typeclass may
define, so the filter compares by `id()`.

`TG-07` fixes the semantics the factory form implies: the filter is a snapshot of the moment it was
built, not a live view. Correct for a single walk, which is all either is used for, and worth stating
because the alternative reading is just as plausible.

`TG-12` diverges from the sibling's convention that a factory built with nothing raises `ValueError`.
There, empty arguments can only be a caller bug. Here an empty record is the ordinary state of a wearer
who had nothing on, and `restore_worn()` reaches it on a normal path.

The end-to-end proof stays where it is — `GW`, `GC`, `RW` and the weight cases exercise these filters
through the methods that use them. The cases above cover them as published units a consumer can pick up
on their own.

### NS — normalising a slot name

`contrib.utils.normalise_slot(text)` reduces a string to the one form typed text and slot names are
compared in: **upper case, with spaces, underscores and hyphens removed.**

Both sides go through it, which is the point. It stops mattering how a consumer spelled the enum — a
game with `RIGHT_FINGER` and a game with `RIGHTFINGER` both answer to `right finger`, `right_finger`,
`Right-Finger` and `rightfinger`, with nothing declared either side.

**The result is for comparison only.** What reaches `wear()` is the real slot value, looked up after
the match; the normalised form is thrown away.

**It lives in contrib because only contrib has typed text.** Core takes a slot name or an enum member
and never sees what a player wrote.

| ID | Case | Test function |
|---|---|---|
| NS-01 | A name already in canonical form is unchanged | test_ns_01_a_canonical_name_is_unchanged |
| NS-02 | Case is folded up | test_ns_02_case_is_folded_up |
| NS-03 | Spaces are removed | test_ns_03_spaces_are_removed |
| NS-04 | Underscores are removed | test_ns_04_underscores_are_removed |
| NS-05 | Hyphens are removed | test_ns_05_hyphens_are_removed |
| NS-06 | Surrounding whitespace is ignored | test_ns_06_surrounding_whitespace_is_ignored |
| NS-07 | Mixed and repeated separators all go | test_ns_07_mixed_and_repeated_separators_all_go |
| NS-08 | An empty string normalises to an empty string | test_ns_08_an_empty_string_normalises_to_empty |

`NS-03` to `NS-05` are one rule and three decisions. An implementation handling only spaces passes the
first and fails the others, which is exactly the partial job worth catching.

`NS-08` is not a curiosity. `wear ring on ` reaches this function with an empty string, and a raise
there is a traceback where a refusal belongs. The command rejects the empty case; this pins that the
normaliser is not where it blows up.

**A consumer naming two slots that normalise the same** — `BACK_PACK` and `BACKPACK` — makes them
permanently ambiguous, and no case here prevents it. Two slots differing only by a separator are a
naming mistake rather than something the library can resolve, and the matcher's own "which do you
mean?" is what a player would get.

### SM — matching a typed slot name

`contrib.utils.match_slot(wearer, text)` turns what a player typed into a slot name this wearer
actually has, or says why it cannot.

Returns `(slot_name, None)` or `(None, refusal)` — the same shape `_resolve_wearable()` uses, so a
command reads the same whether it is resolving an item or a slot. The refusal is a finished message.

**Both sides go through `normalise_slot()`**, so how the consumer spelled the enum stops mattering.

The order:

1. An exact match on the normalised form wins outright. A game with both `HAND` and `LEFT_HAND` needs
   this, or `hand` can never mean `HAND`.
2. Otherwise substring. One hit is the answer.
3. Several hits are a question, and the refusal **names them** — `Which do you mean — left hand or
   right hand?` — in display form, lowercased with underscores as spaces.
4. No hits is a refusal naming what was typed.

**It matches this wearer's slots, not the whole enum.** A humanoid asking for a dog neck is told it has
none rather than told it is ambiguous, and a one-fingered creature is never asked which finger.

| ID | Case | Test function |
|---|---|---|
| SM-01 | An exact slot name matches | test_sm_01_an_exact_slot_name_matches |
| SM-02 | Case and separators are ignored, and the real name comes back | test_sm_02_case_and_separators_are_ignored |
| SM-03 | A substring of one slot name matches it | test_sm_03_a_substring_of_one_slot_matches_it |
| SM-04 | An exact match wins over a substring match | test_sm_04_an_exact_match_wins_over_a_substring |
| SM-05 | A substring matching several slots is refused, and the refusal names them | test_sm_05_several_matches_are_refused_and_named |
| SM-06 | Text matching no slot is refused | test_sm_06_text_matching_no_slot_is_refused |
| SM-07 | A slot the game has but this wearer lacks is refused | test_sm_07_a_slot_this_wearer_lacks_is_refused |
| SM-08 | Empty text is refused rather than matching everything | test_sm_08_empty_text_is_refused |

`SM-02` is where the normaliser earns its place, and it pins that what comes back is the **real** slot
name — `LEFT_HAND`, not the `LEFTHAND` it was compared as. Only the real one can be passed to `wear()`.

`SM-04` is the reason step 1 exists. Without it a slot whose name is contained in another can never be
named on a wearer that has both.

`SM-05` differs from how the item match handles ambiguity, deliberately. Items are not listed because a
match could run to five; a wearer has ten slots in total and a substring rarely hits more than two, so
naming them tells the player exactly which words will work.

`SM-07` is what "this wearer's slots, not the whole enum" means in practice, and it is the case that
fails if the matcher reaches for `valid_slot_names()`.

`SM-08` guards the empty string reaching here from `wear ring on `. Matched as a substring it would hit
every slot; the answer is a refusal, not a list of everything the wearer has.

### CW — the wear command

```
wear <item>
wear <item> on <slot>
```

The command parses, speaks and broadcasts. Everything else is already answered: `match_slot()` turns
the slot text into a name, and `wear()` resolves the item, chooses the slots and returns the message.

**It says almost nothing of its own.** The refusals a player sees come from the mixin or the matcher
verbatim, so there is one wording for "you are already wearing that" rather than one per command.

**The argument splits on the last ` on `.** An item may contain the word — *a ring on a chain* — and
splitting on the first would take the chain for a slot. Splitting on the last is right whenever a slot
was named at all, and is the case the syntax exists for.

| ID | Case | Test function |
|---|---|---|
| CW-01 | No argument asks what to wear | test_cw_01_no_argument_asks_what_to_wear |
| CW-02 | An item name wears it and tells the player | test_cw_02_an_item_name_wears_it |
| CW-03 | A refusal from the mixin reaches the player unchanged | test_cw_03_a_refusal_reaches_the_player_unchanged |
| CW-04 | `on <slot>` wears it in that slot | test_cw_04_on_a_slot_wears_it_there |
| CW-05 | A slot matching nothing is refused, and nothing is worn | test_cw_05_a_slot_matching_nothing_wears_nothing |
| CW-06 | `on` with nothing after it is refused | test_cw_06_on_with_nothing_after_it_is_refused |
| CW-07 | The room is told, and the wearer is not told twice | test_cw_07_the_room_is_told_and_the_wearer_is_not_told_twice |
| CW-08 | Only the last ` on ` splits the argument | test_cw_08_only_the_last_on_splits_the_argument |

`CW-05` is ordered deliberately: the slot is matched **before** `wear()` is called, so a mistyped slot
never puts the item on somewhere else. Matching after would wear it first and then complain.

`CW-07` is what makes it a MUD command rather than a function call. The wearer gets the mixin's
message; everyone else in the room sees the action, and the wearer must not receive both.

`CW-08` pins the split rule with an item whose own name contains ` on `. It is the case that fails on
`partition()` and passes on `rpartition()`.

**Known limitation, deliberately uncovered.** `wear ring on a chain` — where the whole thing is the
item's name and no slot was meant — reads the chain as a slot and refuses. Nothing in the string says
which was intended. A player types `wear ring on a chain on left finger`, or names the item less
ambiguously.

### CM — the remove command

```
remove <item>
remove <item> from <slot>
remove from <slot>
```

The mirror of `CmdWear`, with one form it has no counterpart to: **naming only a slot.** Wearing
nothing into a slot means nothing, but taking off whatever is on the right finger is a complete
instruction, and `remove()` already accepts it.

The parse has to reach that third form. `remove from right finger` leaves ` from right finger` as the
argument, and a split on ` from ` never sees a leading separator — so an argument that *starts* with
`from ` is a slot with no item, and only what remains goes through the usual split on the last
` from `.

| ID | Case | Test function |
|---|---|---|
| CM-01 | No argument asks what to remove | test_cm_01_no_argument_asks_what_to_remove |
| CM-02 | An item name removes it and tells the player | test_cm_02_an_item_name_removes_it |
| CM-03 | A refusal from the mixin reaches the player unchanged | test_cm_03_a_refusal_reaches_the_player_unchanged |
| CM-04 | An item and a slot together remove that item from that slot | test_cm_04_an_item_and_a_slot_remove_from_that_slot |
| CM-05 | A slot alone removes whatever is in it | test_cm_05_a_slot_alone_removes_what_is_in_it |
| CM-06 | A slot matching nothing is refused, and nothing comes off | test_cm_06_a_slot_matching_nothing_removes_nothing |
| CM-07 | `from` with nothing after it is refused | test_cm_07_from_with_nothing_after_it_is_refused |
| CM-08 | The room is told, and the wearer is not told twice | test_cm_08_the_room_is_told_and_the_wearer_is_not_told_twice |
| CM-09 | Only the last ` from ` splits the argument | test_cm_09_only_the_last_from_splits_the_argument |

`CM-05` is the form the whole slot argument was added for. Two rings with the same key, one on each
hand, and `remove ring` takes whichever came first — `remove from right hand` is how a player says
which.

`CM-06` is ordered like `CW-05`: the slot is matched **before** `remove()` is called, so a mistyped
slot never strips something else first.

`CM-08` asserts both halves, which `CW-07` did not until it was mutation-checked. `self.call(...,
receiver=)` returns only the receiver's output, so the wearer being told twice is invisible to it —
the caller's own output has to be captured separately and the phrase counted.

`CM-09` pins the split with an item whose name contains ` from `. The same rule as `CW-08`, and the
same consequence: a wearable's name should hold neither ` on ` nor ` from ` as a spaced word.

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
