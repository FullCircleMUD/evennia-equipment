# Test plan

Every test case the library commits to covering, and the test function that covers it. The library is
built test-first: cases are agreed here, tests are written against them, then the implementation is
written to pass. The **Test function** column is the auditable trail — it is filled in as each test is
written, so an empty cell means the case is agreed but not yet covered.

Case IDs are stable and referenceable. Do not renumber; retire an ID rather than reuse it. Every test
function carries its case ID as its docstring, so the trail reads in both directions.

All test functions live in `src/evennia_equipment/tests.py`.

Behaviour is agreed here first, before any test or code — see
[design-principles.md](../../../design/design-principles.md) § 8.

| Prefix | Covers |
|---|---|
| `SC` | The scaffold — the library is installed and the runner reaches it |
| `CR` | `EquipmentCarriableMixin` — an item's weight, and what may be stored in it |
| `ST` | `stackable` — whether an item is interchangeable with another of its name |
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
| `FC` | `finders.find_carried()` — the item a player names among what they carry and are not wearing |
| `FW` | `finders.find_worn()` — the item a player names among what they are wearing |
| `MS` | `finders.match_slot()` — turning what a player typed into one of their slots |
| `NS` | *Retired — case and separators are `evennia_targeting.parse_match`'s* |
| `SM` | *Retired — matching a typed slot name is `finders.match_slot()`'s* |
| `UW` | `contrib.utils.resolve_wear()` — what a player typed after `wear`, as an item and a slot |
| `UR` | `contrib.utils.resolve_remove()` — what a player typed after `remove`, as an item |
| `CW` | `contrib.commands.CmdWearMixin` and `CmdWear` — the command a player types to put something on |
| `CM` | `contrib.commands.CmdRemoveMixin` and `CmdRemove` — the command a player types to take something off |
| `CE` | `contrib.commands.CmdEquipmentMixin` and `CmdEquipment` — the slot sheet a player reads |
| `CI` | `contrib.commands.CmdInventoryMixin` and `CmdInventory` — what a player is carrying but not wearing |
| `CS` | `contrib.cmdset.EquipmentCmdSet` — the four commands, merged in one line |

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
| `Longsword` | Declares `stackable = False`, as a game with durability does |
| `Humanoid` | A wearer with the humanoid body plan |
| `Dog` | A wearer with a different body plan, so `body_slots` is proved to be read |
| `ShroudedHelmet` | Overrides Evennia's `get_display_name()`, as a game with darkness would |
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
| SC-02 | The log shim binds and a call returns None without raising | test_sc_02_the_log_shim_binds_and_a_call_returns_none |

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

### ST — whether an item stacks

`stackable` says whether this item is interchangeable with another of the same name. **`True` by
default**, and validated in `at_set()` like every other stored value: a non-boolean is refused at the
assignment that made it, rather than quietly making everything stack.

The library never asks *why*. A game with durability sets it `False` on anything that wears — two
longswords are not the same longsword once one is chipped — and the library learns nothing about
durability in the process. Charges, enchantment and ownership are all the same shape.

It exists because a listing has to decide whether to write one line or two, and that is a question only
the game can answer. `contrib`'s `inventory` is the first caller.

| ID | Case | Test function |
|---|---|---|
| ST-01 | Stackable defaults to `True` | test_st_01_stackable_defaults_to_true |
| ST-02 | A subclass can declare it `False` | test_st_02_a_subclass_can_declare_it_false |
| ST-03 | A non-boolean is refused | test_st_03_a_non_boolean_is_refused |

`ST-03` is the mirror of `CR-10`, which refuses a boolean where a number is wanted. Here anything that
is *not* a boolean is refused — `stackable = 1` would work under a truthiness check and mean nothing.

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
| WS-20 | A reconciliation that dropped an occupied slot logs an INFO naming the wearer, the slot and the item that was in it | test_ws_20_a_dropped_occupied_slot_is_logged |
| WS-21 | A reconciliation that only added slots logs an INFO naming the wearer and the added slots | test_ws_21_added_slots_are_logged |
| WS-22 | A load with nothing to reconcile logs nothing | test_ws_22_a_load_with_nothing_to_reconcile_logs_nothing |

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

`WS-20`–`WS-22` are INFO deliberately: a reconciliation is the game working as intended after a body
plan changed, not a fault — the line exists so a player's "my ring stopped working" can be looked up.
An item in a dropped slot stops being worn with no hook fired, and this line is the only witness.
`WS-22` is the noise guard: a line per ordinary load would bury the ones that matter.

### WE — wearing

Two methods: a query that answers where an item would go, and `wear()`, which puts it there.

**`slots_for(item, slot=None)`** returns the group of slots the item would fill on this wearer, or
`None`. It changes nothing and decides nothing.

1. Take the item's groups, in declaration order.
2. With `slot` — an enum member — keep only the groups containing it.
3. Return the first group where **every** slot exists on this wearer and is free.
4. None qualifies — no groups, none containing the slot, none free — returns `None`.

Group order is the item author's preference — `[["RIGHT_FINGER"], ["LEFT_FINGER"]]` favours the right
hand — and the library holds no opinion about it. **`slot` overrides that preference**: a ring goes
on the finger asked for, and a shortsword declaring `[["WIELD"], ["HOLD"]]` can be held. Naming one
slot of a multi-slot group takes the whole group, and only if every slot in it is free — a greatsword
named by the right hand, with something in the left, gets `None`.

**`wear(item, slot=None)`** puts the item on. `item` is the object, already found by the caller, and
the caller has already asked `slots_for(item, slot)` — `wear()` identifies nothing.

1. The item not in `contents` raises.
2. The item already worn raises.
3. `slots_for(item, slot)` — `None` raises.
4. Ask `at_pre_wear(item)`. A refusal returns `(False, reason)`, and nothing changes.
5. Write `worn_items` with that group filled.
6. Call `at_post_wear(item, group)`.
7. Return `(True, "")`.

Each raise is a caller bug, and each stops a state that would otherwise be corrupt: worn but not
carried, worn twice, or a call that silently did nothing.

**`at_pre_wear(item)` is the hook other components veto through** — a class restriction, an alignment
rule, a minimum strength. It returns `(bool, str)`, allows by default, and is asked inside `wear()`, so
every path that puts something on gets the veto — `restore_worn()` included. The reason reaches the
caller unchanged, for the command to tell the player.

| ID | Case | Test function |
|---|---|---|
| WE-01 | A single-slot item fills that slot | test_we_01_a_single_slot_item_fills_that_slot |
| WE-02 | A multi-slot item fills every slot in its group | test_we_02_a_multi_slot_item_fills_every_slot_in_its_group |
| WE-03 | The first group with all its slots free is chosen | test_we_03_the_first_free_group_is_chosen |
| WE-04 | A later group is chosen when an earlier one is occupied | test_we_04_a_later_group_is_chosen_when_the_first_is_taken |
| WE-05 | A partly-blocked group is skipped rather than partly filled | test_we_05_a_partly_blocked_group_is_not_partly_filled |
| WE-06 | A group naming a slot this wearer does not have is skipped | test_we_06_a_group_naming_a_missing_slot_is_skipped |
| WE-11 | Wearing does not move the item out of contents | test_we_11_wearing_does_not_move_the_item |
| WE-12 | Wearing does not change the carried weight | test_we_12_wearing_does_not_change_the_carried_weight |
| WE-23 | A named slot is chosen over an earlier free group | test_we_23_a_named_slot_is_chosen_over_an_earlier_free_group |
| WE-24 | Naming one slot of a multi-slot group fills the whole group | test_we_24_naming_one_slot_of_a_group_fills_the_whole_group |
| WE-30 | `at_pre_wear()` allows wearing by default | test_we_30_at_pre_wear_allows_by_default |
| WE-31 | A consumer refusing stops the wearing and fills no slot | test_we_31_a_consumer_refusing_stops_the_wearing |
| WE-32 | The consumer's reason is what `wear()` returns, with `False` | test_we_32_the_consumers_reason_is_returned |
| WE-33 | `at_post_wear()` sees the slots already filled | test_we_33_at_post_wear_sees_the_slots_already_filled |
| WE-34 | `at_post_wear()` receives the slots that were filled | test_we_34_at_post_wear_receives_the_slots_filled |
| WE-35 | `at_post_wear()` does not fire when wearing is refused | test_we_35_at_post_wear_does_not_fire_when_refused |
| WE-36 | `restore_worn()` fires `at_post_wear()` for each item put back | test_we_36_restore_worn_fires_at_post_wear |
| WE-37 | `slots_for()` returns the group `wear()` fills, and changes nothing | test_we_37_slots_for_returns_the_group_wear_fills |
| WE-38 | `slots_for()` returns `None` for an item declaring no slots | test_we_38_slots_for_is_none_for_an_item_declaring_no_slots |
| WE-39 | `slots_for()` returns `None` when no group is free | test_we_39_slots_for_is_none_when_no_group_is_free |
| WE-40 | `slots_for()` returns `None` for a named slot the item does not declare | test_we_40_slots_for_is_none_for_a_slot_the_item_does_not_declare |
| WE-41 | `slots_for()` returns `None` for a named slot this wearer does not have | test_we_41_slots_for_is_none_for_a_slot_this_wearer_does_not_have |
| WE-42 | `slots_for()` returns `None` for a named slot of a multi-slot group when another slot in the group is occupied | test_we_42_slots_for_is_none_when_a_named_group_is_partly_occupied |
| WE-43 | Wearing an item not in contents raises `ValueError`, fills no slot, and `at_post_wear()` does not fire | test_we_43_wearing_an_item_not_in_contents_raises |
| WE-44 | Wearing an item already worn raises `ValueError`, changes no slot, and `at_post_wear()` does not fire | test_we_44_wearing_an_item_already_worn_raises |
| WE-45 | Wearing with no free group raises `ValueError`, fills no slot, and `at_post_wear()` does not fire | test_we_45_wearing_with_no_free_group_raises |
| WE-47 | Wearing that goes through returns `(True, "")` | test_we_47_wearing_that_goes_through_returns_true_and_no_reason |

`WE-05` is the one that bites if the implementation fills slots as it checks them: a group that turns
out to be blocked half-way through would leave the wearer holding an item in some of its slots and
not others. Selection completes before anything is written.

`WE-12` ties back to the carrying half. Wearing moves a reference, not an object, so the total must
not shift — which is why the two mixins compose without either knowing about the other.

`WE-23` is the case the argument exists for, and the one an implementation that merely *checks* the
named slot would pass by accident. A ring with both fingers free goes on the one that was asked for,
not the one declared first.

`WE-24` fixes what naming a slot means: the group containing it, not the slot alone. A greatsword
named by one hand still takes both.

`WE-37` is the agreement between the caller's check and the placement. A command that asks
`slots_for()`, then calls `wear()`, gets the group it was told about — and asking changes nothing, so
a command may ask and then stop.

`WE-40` and `WE-41` are separate paths to `None`: the item declaring no group with that slot, and the
wearer lacking the slot. The caller tells them apart for its message; both have to answer `None`.

`WE-42` is the two-handed sword wielded by the right hand while the left holds something. It is the
narrowing and the all-free rule together.

`WE-44` is the ring on both hands. Without it, a ring already on the left finger has a free group
left, and `wear()` would put it on the right as well.

`WE-47` is the success half of the return. The reason is empty: the command writes its own success
line.

**The four hooks.** `at_pre_wear(item)` and `at_pre_remove(item)` return `(bool, str)`, allow by
default, and are asked inside `wear()` and `remove()`, after the guards and before anything is written.
`at_post_wear(item, slots)` and `at_post_remove(item, slots)` return nothing and fire once the slots are
written, only when the call went through. The library refuses
nothing of its own in any of them.

They exist because equipment changes a character. A ring of strength is worth nothing until something
recalculates the wearer's strength, and that has to happen on both edges — the library has no idea what
a consumer's stats are, and a consumer has no other moment to learn that the set of worn items changed.

`WE-33` is the ordering that makes them usable: the slots are already written when `at_post_wear` runs,
so a consumer recalculating from `get_all_worn()` sees the item it was told about.

`WE-34` is why the slots are passed. A consumer can read `worn_items` at post-wear, but `RM-33`'s
mirror cannot — by then the slots are freed and where the item *was* exists nowhere else. Passing them
on both sides keeps the pair symmetrical.

`WE-36` is the case that matters after a shard move. Restoring rebuilds the worn set through `wear()`,
so the bonuses come back with it.

Retired: `WE-07` to `WE-10`, `WE-13` to `WE-22`, `WE-25` to `WE-29` and `WE-46`. Resolving a typed
name, and refusing on anything but the hook, are the caller's now; a slot is an enum member. The IDs
are not reused.

### RM — removing

`remove(item)` frees every slot the item occupies and leaves it in `contents`. Taking something off
does not put it down.

**`item` is the object, already identified by the caller** — a command finds it by name or reads it
out of a slot before calling. `remove()` identifies nothing.

1. Gather every slot the item occupies, by identity.
2. None — the item is not worn — raises. The caller should have settled that, so reaching here is a
   caller bug.
3. Ask `at_pre_remove(item)`. A refusal returns `(False, reason)`, and nothing changes.
4. Write `worn_items` with those slots freed.
5. Call `at_post_remove(item, slots)`.
6. Return `(True, "")`.

**`at_pre_remove(item)` is the hook other components veto through** — a curse, a paralysed wearer, a
combat rule. It returns `(bool, str)`, allows by default, and is asked inside `remove()`, so every path
that takes something off gets the veto. The reason reaches the caller unchanged, for the command to
tell the player.

**On the wearer rather than the item**, deliberately. A cursed item is the item's business, but "you
are paralysed" is the wearer's, and an item-side hook cannot express it. A consumer wanting item-side
logic delegates to the item in one line.

| ID | Case | Test function |
|---|---|---|
| RM-01 | Removing frees the slot | test_rm_01_removing_frees_the_slot |
| RM-02 | Removing a multi-slot item frees every slot it occupied | test_rm_02_removing_frees_every_slot_it_occupied |
| RM-04 | Removing leaves the item in contents | test_rm_04_removing_leaves_the_item_in_contents |
| RM-05 | Removing does not change the carried weight | test_rm_05_removing_does_not_change_the_carried_weight |
| RM-06 | Other worn items are unaffected | test_rm_06_other_worn_items_are_unaffected |
| RM-07 | A removed item can be worn again | test_rm_07_a_removed_item_can_be_worn_again |
| RM-09 | Removing one of two identical items frees only that one | test_rm_09_removing_one_of_two_identical_items_frees_only_that_one |
| RM-10 | `at_pre_remove()` allows removal by default | test_rm_10_the_hook_allows_removal_by_default |
| RM-11 | A consumer refusing stops the removal and the item stays worn | test_rm_11_a_consumer_refusing_stops_the_removal |
| RM-12 | The consumer's reason is what `remove()` returns, with `False` | test_rm_12_the_consumers_reason_is_returned |
| RM-13 | The slots are untouched when removal is refused | test_rm_13_the_slots_are_untouched_when_removal_is_refused |
| RM-32 | `at_post_remove()` sees the slots already freed | test_rm_32_at_post_remove_sees_the_slots_already_freed |
| RM-33 | `at_post_remove()` receives the slots that were freed | test_rm_33_at_post_remove_receives_the_slots_freed |
| RM-34 | `at_post_remove()` does not fire when removal is refused | test_rm_34_at_post_remove_does_not_fire_when_refused |
| RM-35 | Removing an item that is not worn raises `ValueError`, the slots are untouched and `at_post_remove()` does not fire | test_rm_35_removing_an_item_not_worn_raises |
| RM-37 | A removal that goes through returns `(True, "")` | test_rm_37_a_removal_that_goes_through_returns_true_and_no_reason |

`RM-02` is the counterpart to `WE-02`: a two-handed item sits under two keys, and freeing only the
first leaves a phantom holding the other hand for good.

`RM-06` catches the lazy implementation — clearing the whole stored dict passes `RM-01` and `RM-02`
while quietly stripping everything else the wearer had on.

`RM-07` is the round trip. An item whose slots are freed but which is still referenced somewhere else
reads as worn, so `wear()` refuses it — a failure neither `RM-01` nor `WE-08` sees on its own.

`RM-09` is about identity rather than equality. A consumer's typeclass may define `__eq__` — by key,
or by a token id — and comparing slots with `==` would then clear every slot holding an item that
merely *compares* equal. The comparison is `is`, and this is the case that says so.

`RM-13` is the counterpart to `WE-05`: a refusal leaves the slots exactly as they were, not
half-freed.

`RM-33` is the reason the post hooks are given slots at all. At post-remove the slots are freed, and
where the item sat exists nowhere else.

`RM-34` is the pairing `WE-35` makes on the other side. A refused removal leaves a consumer's stats
alone; a post hook that fired anyway would strip a ring's bonus from a character still wearing it.

`RM-35` is the guard, and it comes before the hook. Without it an unworn item frees nothing and
`at_post_remove()` still fires, telling the consumer to undo a bonus that was never applied.

`RM-37` is the success half of the return. The reason is empty: the command writes its own success
line.

Retired: `RM-03`, `RM-08`, `RM-14` to `RM-31` and `RM-36`. Resolving a typed name and taking a slot
are the caller's now. The IDs are not reused.

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
| ER-08 | A skipped identity-less item logs a WARN naming the wearer, the item and the attribute | test_er_08_a_skipped_item_is_logged_as_a_warn |
| ER-09 | Recording identified items logs nothing | test_er_09_recording_identified_items_logs_nothing |

`ER-05` is what makes it a record of the present rather than a history. An append-only implementation
passes every other case here and slowly accumulates gear the character no longer owns, which restore
would then look for and never find.

`ER-07` is the case the word "cache" would have talked us out of. A record that does not survive the
archive is worth nothing, since surviving the archive is the only reason it exists.

`ER-08` is WARN where the library's other lines are INFO. Skipping is tolerated behaviour — `ER-04`
pins it — but this method only runs in a game that archives, and such a game has declared worn gear
restorable, so a worn item with no identity means its identity system is broken. The line names the
attribute because the worst case — the setting pointing at something no item carries — skips every
item, and a burst of these at archive time is the only signal before a restore comes back empty.

### RW — putting the equipment back on

`restore_worn()` walks `contents` and wears anything whose identity is in the record. A consumer calls
it after their own restore has put the items back — the library has no way to know when that is.

**It walks `contents`, not the record.** An identity matching nothing is then never visited, so there
is nothing to ignore explicitly and no case for it.

For each item it finds, it is a caller of `wear()` like any other:

1. Already worn — refused, `already wearing`.
2. `slots_for(item)` is `None` — refused, `nowhere to wear`.
3. Otherwise `wear(item)`, with no slot: the item goes into its default group. `at_pre_wear` is asked
   there, and its refusal comes back as `(False, reason)`.

Every outcome is a `(bool, str)`, returned in a list and never sent to the player — a refusal just
leaves the item carried. The record holds identities, not slots, so a ring worn on the right finger
can come back on the left.

**Order does not matter.** The items all fitted simultaneously when the record was written, so they
all fit now, whatever order `contents` gives them. No sorting, no second pass, no rollback.

| ID | Case | Test function |
|---|---|---|
| RW-01 | An item whose identity is in the record is worn | test_rw_01_an_item_in_the_record_is_worn |
| RW-02 | An item not named in the record stays carried | test_rw_02_an_item_not_in_the_record_stays_carried |
| RW-03 | An item already worn is refused, not raised, and the refusal says so | test_rw_03_an_item_already_worn_is_refused |
| RW-04 | An item with nowhere to go is refused, not raised, and stays carried | test_rw_04_an_item_with_nowhere_to_go_is_refused |
| RW-05 | The record is unchanged by restoring | test_rw_05_the_record_is_unchanged_by_restoring |
| RW-06 | An item that is not wearable at all is passed over | test_rw_06_an_item_that_is_not_wearable_is_passed_over |
| RW-07 | A refused restore logs an INFO naming the wearer, the item and the refusal | test_rw_07_a_refused_restore_is_logged |
| RW-08 | A restore where every item goes on logs nothing | test_rw_08_a_clean_restore_logs_nothing |
| RW-09 | An `at_pre_wear()` refusal is returned, and the item stays carried | test_rw_09_an_at_pre_wear_refusal_is_returned |

`RW-04`'s real trigger is a slot removed from `body_slots` since the record was written. The item comes
back carried rather than worn, and the refusal says why — which is the whole diagnostic a consumer
gets.

`RW-03` means calling it twice reports every item as a failure the second time. That is correct for
one call per restore, which is the intended use, and worth knowing rather than discovering: under
`evennia-scaling` this runs on every shard move.

`RW-06` is the ordinary case that walking `contents` invites. A character carries rocks and bread as
well as armour, and a plain carriable item has no `wearslot_identity` to ask about — reading one
raises rather than returning `None`.

`RW-07` is INFO, not WARN: a refused restore is the mechanism working on state that changed
underneath it, and the same refusal is already returned to the caller. The log line is durability —
it survives a consumer that discards the list, so "my gear came back unworn" can be looked up.
`RW-08` is the noise guard: a clean restore is the ordinary case and says nothing.

`RW-09` is the hook path. A restriction that changed since the record was written — a class the
character no longer has — keeps the item off, the same as it would through a command.

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

### FC — finding something carried

`finders.find_carried(caller, text)` finds the item `text` names among what `caller` carries and is
not wearing. It is for any command that acts on something in a player's inventory — wearing it,
enchanting it, giving it away.

Returns `(item, None)`, or `(None, refusal)` with a finished message. It messages no one: the command
speaks.

1. `text` empty — refused, rather than matching everything.
2. Candidates are the caller's carried items: `walk_contents` over `op_not(f_worn_by(caller))`.
3. Matching is Evennia's own, `caller.search(text, candidates=..., quiet=True)` — key or alias, any
   case, and `sword-2` for the second of several.
4. One match, or several sharing a key, is the answer — items sharing a key are interchangeable, so the
   first is taken.
5. Several with differing keys — refused, `Which <text> do you mean?`.
6. None carried, but a worn item matches — refused naming the worn item, which is a more useful answer
   than "not carrying".
7. Nothing matches — refused, `You are not carrying <text>.`

| ID | Case | Test function |
|---|---|---|
| FC-01 | A name matching one carried item returns it | test_fc_01_a_name_matching_one_carried_item_returns_it |
| FC-02 | A worn item is never returned | test_fc_02_a_worn_item_is_never_returned |
| FC-03 | A name matches through `caller.search` — an alias matches, in any case | test_fc_03_a_name_matches_through_caller_search |
| FC-04 | Several carried items sharing a key return the first | test_fc_04_several_sharing_a_key_return_the_first |
| FC-05 | Several with differing keys are refused, asking which, with what was typed | test_fc_05_differing_keys_are_refused_asking_which |
| FC-06 | `<name>-2` returns the second of several | test_fc_06_a_numbered_name_returns_that_one |
| FC-07 | A name matching only a worn item is refused, naming that item as worn | test_fc_07_a_name_matching_only_a_worn_item_says_it_is_worn |
| FC-08 | A name matching nothing is refused, with what was typed | test_fc_08_a_name_matching_nothing_is_refused |
| FC-09 | Empty text is refused | test_fc_09_empty_text_is_refused |
| FC-10 | Nothing is sent to the caller | test_fc_10_nothing_is_sent_to_the_caller |
| FC-11 | A `#dbref` of something not carried is not found, even for a caller allowed dbref searches | test_fc_11_a_dbref_of_something_not_carried_is_not_found |

`FC-03` pins that the matching is Evennia's, not this library's. Exact-before-partial and word starts
are `caller.search`'s to prove.

`FC-06` is what `caller.search` buys over a plain key filter: the only way a player can pick between
two identical items without naming a slot.

`FC-07` is the two-place answer. A player wearing the helmet and typing `wear helmet` is told they are
wearing it, not that they have no such thing.

`FC-10` is the `quiet=True`. Without it `caller.search` messages the caller itself, and the command's
refusal arrives as a second message.

`FC-11` is the `use_dbref=False`. A `#dbref` makes Evennia's search global and ignores the candidates,
so a builder typing `enchant #12` would otherwise get an object from anywhere in the game. The caller
has Builder permission, because that is who dbref searches are open to.

### FW — finding something worn

`finders.find_worn(caller, text)` is `find_carried()`'s mirror: the item `text` names among what
`caller` is wearing. The candidates are `walk_contents` over `f_worn_by(caller)`; the matching, the
return shape and the silence are the same.

A name matching only a carried item is refused naming it as not worn; nothing matching is refused as
not carried.

| ID | Case | Test function |
|---|---|---|
| FW-01 | A name matching one worn item returns it | test_fw_01_a_name_matching_one_worn_item_returns_it |
| FW-02 | A carried item that is not worn is never returned | test_fw_02_a_carried_item_is_never_returned |
| FW-03 | Several worn items sharing a key return the first | test_fw_03_several_sharing_a_key_return_the_first |
| FW-04 | Several with differing keys are refused, asking which, with what was typed | test_fw_04_differing_keys_are_refused_asking_which |
| FW-05 | `<name>-2` returns the second of several | test_fw_05_a_numbered_name_returns_that_one |
| FW-06 | A name matching only a carried item is refused, naming that item as not worn | test_fw_06_a_name_matching_only_a_carried_item_says_not_worn |
| FW-07 | A name matching nothing is refused, with what was typed | test_fw_07_a_name_matching_nothing_is_refused |
| FW-08 | Empty text is refused | test_fw_08_empty_text_is_refused |
| FW-09 | Nothing is sent to the caller | test_fw_09_nothing_is_sent_to_the_caller |

`FW-06` is `FC-07` from the other side: a player holding the boots and typing `remove boots` is told
they are not wearing them.

### MS — matching a typed slot name

`finders.match_slot(caller, text)` turns what a player typed into a member of the slot enum, from the
slots `caller` actually has.

Returns `(member, None)`, or `(None, refusal)`. The member is what `wear()` and `slots_for()` take.

**The matching is `evennia_targeting.parse_match(..., substring=True)`** over the keys of the caller's
`worn_items`. It ignores case, spaces, underscores and hyphens, so `left ring finger` and
`LEFT_RING_FINGER` are the same. One match is the answer. Several are refused, naming them — lowercased,
underscores as spaces. None is refused naming what was typed.

**It matches this caller's slots, not the whole enum.** A humanoid typing `pet neck` is told it has
none.

| ID | Case | Test function |
|---|---|---|
| MS-01 | Case and separators are ignored, and the enum member comes back | test_ms_01_case_and_separators_are_ignored_and_the_member_returned |
| MS-02 | Text matching several of the caller's slots is refused, naming them | test_ms_02_several_matches_are_refused_and_named |
| MS-03 | Text matching no slot is refused, with what was typed | test_ms_03_text_matching_no_slot_is_refused |
| MS-04 | A slot the enum has but this caller lacks is refused as matching nothing | test_ms_04_a_slot_this_caller_lacks_is_refused |
| MS-05 | Empty text is refused | test_ms_05_empty_text_is_refused |

`MS-01` pins the member, not the string. `wear()` takes a member, and a string handed on would fail
there rather than here.

`MS-04` is what "this caller's slots" means, and the case that fails if the matcher reaches for the
whole enum.

`MS-05` guards `wear ring on ` — an empty string matched as a substring would hit every slot.

The exact, word-start and substring order is `parse_match`'s, covered by its `PM` cases in
`evennia-targeting`.

### NS — retired

Retired: `NS-01` to `NS-08`. Ignoring case, spaces, underscores and hyphens when a typed slot name is
compared is `evennia_targeting.parse_match`'s, and its `PM` cases cover it.

### SM — retired

Retired: `SM-02` and `SM-05` to `SM-08`, with `contrib.utils.match_slot()`. Matching a typed slot name
is the core `finders.match_slot()`'s, and its `MS` cases cover it.

### UW — resolving what to wear

`contrib.utils.resolve_wear(caller, text)` turns what a player typed after `wear` into the item and the
slot `wear()` takes.

Returns `((item, slot), None)`, or `(None, refusal)`. `slot` is an enum member, or `None` when none was
named.

1. `parse_split(text, "on")` — the item text, and the slot text if `on` was typed.
2. Slot text given — `finders.match_slot()`. Its refusal is returned unchanged. The slot is matched
   first, so a mistyped slot never reaches the item lookup.
3. `finders.find_carried()` on the item text. Its refusal is returned unchanged.

| ID | Case | Test function |
|---|---|---|
| UW-01 | An item name alone returns the carried item and no slot | test_uw_01_an_item_name_alone_returns_the_item_and_no_slot |
| UW-02 | `<item> on <slot>` returns the item and the slot's enum member | test_uw_02_an_item_on_a_slot_returns_both |
| UW-03 | A slot that matches nothing is refused with `match_slot()`'s refusal | test_uw_03_a_slot_matching_nothing_is_refused_with_match_slots_refusal |
| UW-04 | An item that is not carried is refused with `find_carried()`'s refusal | test_uw_04_an_item_not_carried_is_refused_with_find_carrieds_refusal |

How the text splits — the last whole-word `on`, in any case — is `parse_split`'s, covered by its own
cases in `evennia-targeting`.

### UR — resolving what to remove

`contrib.utils.resolve_remove(caller, text)` turns what a player typed after `remove` into the item
`remove()` takes.

Returns `(item, None)`, or `(None, refusal)`.

1. `parse_split(text, "from")` — the item text, and the slot text if `from` was typed. Nothing before
   `from` is the slot-only form.
2. Slot text given — `finders.match_slot()`, then the item in that slot. An empty slot is refused.
   With item text too, the item in the slot must match it: that is how a player says which of two
   identical rings.
3. No slot — `finders.find_worn()` on the item text. Its refusal is returned unchanged.

| ID | Case | Test function |
|---|---|---|
| UR-01 | An item name alone returns the worn item | test_ur_01_an_item_name_alone_returns_the_worn_item |
| UR-02 | `from <slot>` returns whatever is in that slot | test_ur_02_a_slot_alone_returns_what_is_in_it |
| UR-03 | `<item> from <slot>` returns the item in that slot, of two sharing a key | test_ur_03_an_item_from_a_slot_returns_the_one_in_that_slot |
| UR-04 | `from <slot>` on an empty slot is refused | test_ur_04_an_empty_slot_is_refused |
| UR-05 | `<item> from <slot>`, with something else in the slot, is refused | test_ur_05_a_slot_holding_something_else_is_refused |
| UR-06 | A slot that matches nothing is refused with `match_slot()`'s refusal | test_ur_06_a_slot_matching_nothing_is_refused_with_match_slots_refusal |
| UR-07 | An item that is not worn is refused with `find_worn()`'s refusal | test_ur_07_an_item_not_worn_is_refused_with_find_worns_refusal |

`UR-03` is the case the slot form exists for. Two rings sharing a key, one on each hand: the name alone
takes the first, and the slot is the only way to say which.

### CW — the wear command

`contrib.commands.CmdWearMixin` is the command's behaviour, for a game to compose onto its own command
class:

```python
class CmdWear(CmdWearMixin, Command):
    key = "wear"
```

`contrib.commands.CmdWear` is exactly that over Evennia's `Command`, so `EquipmentCmdSet` still works
as it ships.

```
wear <item>
wear <item> on <slot>
```

1. No argument — `Wear what?`.
2. `resolve_wear()`. A refusal is told to the caller.
3. `slots_for(item, slot)` is `None` — refused: not wearable at all, can't go on the named slot, or
   nowhere free.
4. `wear(item, slot)`. `at_pre_wear`'s refusal is told to the caller unchanged.
5. The caller is told they wear it, `announce(item)` tells the room, and `at_success(item)` runs.

**Two seams, each doing one job.** `announce(item)` tells the room, with `msg_contents` by default; a
game with its own messaging overrides it. `at_success(item)` does nothing by default; a game whose
wearing costs a turn in a fight starts its time wait there. Both run only when the item went on.

| ID | Case | Test function |
|---|---|---|
| CW-01 | No argument asks what to wear | test_cw_01_no_argument_asks_what_to_wear |
| CW-02 | An item name wears it and tells the player | test_cw_02_an_item_name_wears_it |
| CW-03 | An `at_pre_wear` refusal reaches the player unchanged | test_cw_03_an_at_pre_wear_refusal_reaches_the_player_unchanged |
| CW-04 | `on <slot>` wears it in that slot | test_cw_04_on_a_slot_wears_it_there |
| CW-05 | A slot matching nothing is refused, and nothing is worn | test_cw_05_a_slot_matching_nothing_wears_nothing |
| CW-06 | `on` with nothing after it is refused | test_cw_06_on_with_nothing_after_it_is_refused |
| CW-07 | The room is told, and the wearer is not told twice | test_cw_07_the_room_is_told_and_the_wearer_is_not_told_twice |
| CW-10 | An item with nowhere free is refused, and nothing is worn | test_cw_10_an_item_with_nowhere_free_is_refused |
| CW-11 | An item that declares no slots is refused as not wearable | test_cw_11_an_item_declaring_no_slots_is_refused_as_not_wearable |
| CW-12 | An item that cannot go on the named slot is refused, naming the slot | test_cw_12_an_item_that_cannot_go_on_the_named_slot_is_refused |
| CW-13 | The room is told the item's name, not what was typed | test_cw_13_the_room_is_told_the_items_name_not_what_was_typed |
| CW-14 | `announce()` is the room line: overriding it replaces the default | test_cw_14_announce_is_the_room_line |
| CW-15 | `at_success()` runs once when the item goes on, and not on a refusal | test_cw_15_at_success_runs_once_on_success_and_not_on_a_refusal |
| CW-16 | `CmdWear` is `CmdWearMixin` over Evennia's `Command` | test_cw_16_cmdwear_is_the_mixin_over_evennias_command |

`CW-07` asserts both halves. `self.call(..., receiver=)` returns only the receiver's output, so the
wearer being told twice is invisible to it — the caller's own output is captured separately and the
phrase counted.

`CW-13` is `wear helm`, typed for an iron helmet. The room reads the helmet.

`CW-15` is where a game's time wait goes. Running on a refusal would charge a turn for nothing.

Retired: `CW-08` and `CW-09`. How the argument splits is `parse_split`'s.

### CM — the remove command

`contrib.commands.CmdRemoveMixin`, and `contrib.commands.CmdRemove` over Evennia's `Command`, as for
wearing.

```
remove <item>
remove <item> from <slot>
remove from <slot>
```

1. No argument — `Remove what?`.
2. `resolve_remove()`. A refusal is told to the caller.
3. `remove(item)`. `at_pre_remove`'s refusal is told to the caller unchanged.
4. The caller is told they remove it, `announce(item)` tells the room, and `at_success(item)` runs.

| ID | Case | Test function |
|---|---|---|
| CM-01 | No argument asks what to remove | test_cm_01_no_argument_asks_what_to_remove |
| CM-02 | An item name removes it and tells the player | test_cm_02_an_item_name_removes_it |
| CM-03 | An `at_pre_remove` refusal reaches the player unchanged | test_cm_03_an_at_pre_remove_refusal_reaches_the_player_unchanged |
| CM-04 | An item and a slot together remove that item from that slot | test_cm_04_an_item_and_a_slot_remove_from_that_slot |
| CM-05 | A slot alone removes whatever is in it | test_cm_05_a_slot_alone_removes_what_is_in_it |
| CM-06 | A slot matching nothing is refused, and nothing comes off | test_cm_06_a_slot_matching_nothing_removes_nothing |
| CM-07 | `from` with nothing after it is refused | test_cm_07_from_with_nothing_after_it_is_refused |
| CM-08 | The room is told, and the wearer is not told twice | test_cm_08_the_room_is_told_and_the_wearer_is_not_told_twice |
| CM-11 | The room is told the item's name, not the slot that was typed | test_cm_11_the_room_is_told_the_items_name_not_the_slot |
| CM-12 | `announce()` is the room line: overriding it replaces the default | test_cm_12_announce_is_the_room_line |
| CM-13 | `at_success()` runs once when the item comes off, and not on a refusal | test_cm_13_at_success_runs_once_on_success_and_not_on_a_refusal |
| CM-14 | `CmdRemove` is `CmdRemoveMixin` over Evennia's `Command` | test_cm_14_cmdremove_is_the_mixin_over_evennias_command |

`CM-05` is the form the slot argument was added for. Two rings with the same key, one on each hand —
`remove from right hand` is how a player says which.

`CM-11` is `remove from left hand`. The room reads the ring, not a hand.

Retired: `CM-09` and `CM-10`. How the argument splits is `parse_split`'s.

### CE — the equipment command

`contrib.commands.CmdEquipmentMixin` is the command's behaviour, for a game to compose onto its own
command class, and `CmdEquipment` is that mixin over Evennia's `Command`, as for wearing.

```
equipment
eq
```

Every slot the wearer has, in the order its body plan declares them, with what is in it:

```
Equipped Items

  <Head>        an iron helmet
  <Body>
  <Left Hand>   a greatsword
  <Right Hand>  a greatsword
```

**Items are named through `get_display_name(caller)`.** That is Evennia's own viewer-aware hook, so a
game whose items read differently in the dark gets it here without this library providing a seam — and
gets it in `look` and everywhere else at the same time. A hook of ours would be a second, worse
version of it.

**The column is computed, not fixed.** Width comes from the longest slot name this wearer has, so a
body plan with `LEFT_SHOULDER_PAULDRON` still aligns. The gap after it is a class attribute, so a game
can widen it by subclassing rather than by reimplementing.

**An empty slot shows its name and nothing else.** Not "empty", not "nothing" — the absence is the
information, and a word for it would be noise on every line a player has not filled.

| ID | Case | Test function |
|---|---|---|
| CE-01 | Every slot the wearer has is listed | test_ce_01_every_slot_is_listed |
| CE-02 | Slots appear in the order the body plan declares them | test_ce_02_slots_appear_in_declaration_order |
| CE-03 | An empty slot shows its name and nothing else | test_ce_03_an_empty_slot_shows_its_name_and_nothing_else |
| CE-04 | A worn item is named beside its slot | test_ce_04_a_worn_item_is_named_beside_its_slot |
| CE-05 | The item is named through `get_display_name()` | test_ce_05_the_item_is_named_through_get_display_name |
| CE-06 | A multi-slot item appears under every slot it fills | test_ce_06_a_multi_slot_item_appears_under_every_slot |
| CE-07 | Slot names are title-cased with underscores as spaces | test_ce_07_slot_names_are_title_cased_without_underscores |
| CE-08 | Item names align to the longest slot name | test_ce_08_item_names_align_to_the_longest_slot_name |
| CE-09 | `CmdEquipment` is `CmdEquipmentMixin` over Evennia's `Command` | test_ce_09_cmdequipment_is_the_mixin_over_evennias_command |

`CE-02` matters because `worn_items` is rebuilt in `body_slots` order by `at_init()`, and a sheet that
reordered them would make a familiar list unreadable after a slot was added.

`CE-05` is the case that proves the seam is Evennia's rather than ours. It uses a fixture overriding
`get_display_name()`, which is what a game with darkness or blindness does.

`CE-06` records the repetition rather than hiding it. A greatsword under both hands reads oddly, but
`worn_items` genuinely holds it twice, and a sheet that showed it once would leave a hand looking free.
Collapsing it is a judgement about wording, which is the consumer's.

`CE-08` is what makes it a column rather than a list. It fails on any implementation using a fixed
width smaller than the longest name.

### CI — the inventory command

`contrib.commands.CmdInventoryMixin` is the command's behaviour, for a game to compose onto its own
command class, and `CmdInventory` is that mixin over Evennia's `Command`.

```
inventory
inv
i
```

What the wearer is carrying and not wearing, then whatever the consumer adds, then the carrying
summary:

```
Inventory:

  a healing potion (3)
  an iron helmet

  8 gold, 12 wheat          <- extra_lines(), empty by default

Carrying 12.5 of 40.0.
```

**This is the one command with a seam**, and it earns it on the rule the rest of contrib is held to: a
named caller that needs it, and a position no override could reach. A game's fungible balances —
currency, resources — are more items in the listing rather than a footer after it, so they belong
between the items and the summary. `extra_lines()` returns `[]`, and a consumer returns its own.

**An item stacks if it says it does.** `stackable` is `True` by default, so two things with one key
become one line and a count. A game with durability, charges or ownership sets it `False` on those
items, and each then gets its own line — two longswords are not the same longsword once one is chipped,
and only the game knows that.

**The carried items are found and grouped with `bucket_contents`** from `evennia_targeting`, over the
caller's `contents`, filtered by `op_not(f_worn_by(caller))` — one walk that filters and groups
together. A stackable item's bucket is its key; an unstackable one gets a bucket of its own.

**Stacking is by key, not by displayed name.** Stacking by what is shown would merge two different
things a looker cannot make out into one count that counts nothing real. The name is rendered per group
through `get_display_name()` afterwards.

**The summary names a limit only when there is one.** Capacity defaults to `float("inf")`, so a game
that never sets one would otherwise read `Carrying 12.5 of inf.`

| ID | Case | Test function |
|---|---|---|
| CI-01 | Carried items are listed | test_ci_01_carried_items_are_listed |
| CI-02 | A worn item is not listed | test_ci_02_a_worn_item_is_not_listed |
| CI-03 | Stackable items sharing a key are one line with a count | test_ci_03_stackable_items_sharing_a_key_are_one_line |
| CI-04 | Items are named through `get_display_name()` | test_ci_04_items_are_named_through_get_display_name |
| CI-05 | Stacking is by key, not by displayed name | test_ci_05_stacking_is_by_key_not_by_displayed_name |
| CI-12 | An unstackable item is listed on its own | test_ci_12_an_unstackable_item_is_listed_on_its_own |
| CI-13 | Two unstackable items sharing a key are two lines | test_ci_13_two_unstackable_items_sharing_a_key_are_two_lines |
| CI-14 | Stackable and unstackable items are listed together | test_ci_14_stackable_and_unstackable_are_listed_together |
| CI-06 | Carrying nothing says so | test_ci_06_carrying_nothing_says_so |
| CI-07 | `extra_lines()` returns nothing by default | test_ci_07_extra_lines_is_empty_by_default |
| CI-08 | A consumer's extra lines appear between the items and the summary | test_ci_08_extra_lines_appear_between_items_and_summary |
| CI-09 | The summary gives the weight carried | test_ci_09_the_summary_gives_the_weight_carried |
| CI-10 | The summary names the limit when one is set | test_ci_10_the_summary_names_the_limit_when_one_is_set |
| CI-11 | The summary omits the limit when capacity is unlimited | test_ci_11_the_summary_omits_an_unlimited_limit |
| CI-15 | `CmdInventory` is `CmdInventoryMixin` over Evennia's `Command` | test_ci_15_cmdinventory_is_the_mixin_over_evennias_command |

`CI-02` is the whole reason this replaces Evennia's `CmdInventory`, which lists `contents` and so shows
a player their armour as though it were in a sack.

`CI-05` is the case that decides between two readings of "stack by name": two items with different
keys that this looker makes out as the same thing — both `something`. They stay two lines. Stacking by
displayed name would merge them.

`CI-13` is the case `stackable` exists for, and the one no rule inside a command could reach. Two
longswords with the same name and different durability are two things to their owner and one thing to
anything comparing names. The item answers, because only the game knows.

`CI-14` is the mixture, which is the ordinary inventory: potions stacked, weapons not. It fails on an
implementation that picks one rule for the whole listing rather than asking each item.

`CI-08` pins the position rather than the existence. Appending after the summary would be easy and
wrong: a balance is a thing you are carrying, and belongs above the line that totals what you carry.

`CI-11` is what stops the default configuration looking broken. A game with no capacity limit is the
ordinary case, not an edge one.

### CS — the command set

`EquipmentCmdSet` holds the four commands, so a consumer merges one thing:

```python
class CharacterCmdSet(default_cmds.CharacterCmdSet):
    def at_cmdset_creation(self):
        super().at_cmdset_creation()
        self.add(EquipmentCmdSet)
```

**It is a convenience, not a requirement.** A game wanting three of the four adds those individually,
and one replacing `inventory` adds its own after ours. Both are ordinary Evennia and need nothing here.

**Merging is by key**, which is what makes `inventory` a replacement rather than a rival. Evennia's own
`CmdInventory` shares the key, and the set added later wins — so a consumer following the snippet above
gets ours without removing anything.

| ID | Case | Test function |
|---|---|---|
| CS-01 | The set carries all four commands | test_cs_01_the_set_carries_all_four_commands |
| CS-02 | Merged over Evennia's defaults, our `inventory` is the one that answers | test_cs_02_our_inventory_wins_over_evennias |
| CS-03 | A character carrying the set can run a command from it | test_cs_03_a_character_carrying_the_set_can_run_a_command |

`CS-01` is the case that fails when a fifth command is written and nobody adds it to the set — the
command works, its own cases pass, and no player can reach it.

`CS-02` is the whole reason the set exists rather than four imports. It fails if the merge leaves
Evennia's `CmdInventory` answering, which looks like nothing being wrong: a player types `inventory`,
gets a listing, and it is the wrong one — their worn armour shown as though it were in a sack.

`CS-03` proves the wiring end to end. Every command has its own cases, but those call the command
object directly; this is the only one that goes through a cmdset.

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
