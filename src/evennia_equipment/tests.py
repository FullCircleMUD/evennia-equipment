# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for evennia-equipment. Run via ``python runtests.py``.

Every test carries its case ID from docs/test-plan.md as its docstring, so
the coverage trail reads in both directions.
"""

from unittest import TestCase, mock

from django.test import TestCase as DjangoTestCase

import evennia_equipment
from evennia_equipment.log import equipment_log


class ScaffoldTests(TestCase):
    """SC — the library is installed and the runner reaches it."""

    def test_sc_01_the_package_is_importable_and_versioned(self):
        """SC-01"""
        self.assertTrue(evennia_equipment.__version__)

    def test_sc_02_the_log_shim_is_a_no_op_outside_evennia(self):
        """SC-02"""
        self.assertIsNone(equipment_log("scaffold check"))


class CarriableTests(DjangoTestCase):
    """CR — an item's weight, and what may be stored in it."""

    def _thing(self, typeclass=None):
        """Create one carriable object. Not a test.

        ``nohome=True`` because this suite builds no world. Evennia's default
        home is #2 (Limbo), which nothing here creates, and the foreign key to
        it is checked when the test transaction closes.
        """
        from evennia import create_object
        from tests.game_typeclasses import CarriableThing

        return create_object(typeclass or CarriableThing, key="thing", nohome=True)

    def test_cr_01_weight_defaults_to_zero(self):
        """CR-01"""
        self.assertEqual(self._thing().weight, 0.0)

    def test_cr_02_a_subclass_can_override_the_default_weight(self):
        """CR-02"""
        from tests.game_typeclasses import HeavyThing

        self.assertEqual(self._thing(HeavyThing).weight, 3.0)

    def test_cr_03_two_instances_hold_independent_weights(self):
        """CR-03"""
        first, second = self._thing(), self._thing()
        first.weight = 2.0
        self.assertEqual(first.weight, 2.0)
        self.assertEqual(second.weight, 0.0)

    def test_cr_04_a_float_weight_is_stored_as_given(self):
        """CR-04"""
        thing = self._thing()
        thing.weight = 1.5
        self.assertEqual(thing.weight, 1.5)

    def test_cr_05_an_int_weight_reads_back_as_a_float(self):
        """CR-05"""
        thing = self._thing()
        thing.weight = 5
        self.assertEqual(thing.weight, 5.0)
        self.assertIsInstance(thing.weight, float)

    def test_cr_06_a_weight_of_zero_is_accepted(self):
        """CR-06"""
        thing = self._thing()
        thing.weight = 0
        self.assertEqual(thing.weight, 0.0)

    def test_cr_07_a_negative_weight_is_refused(self):
        """CR-07"""
        thing = self._thing()
        with self.assertRaises(AttributeError):
            thing.weight = -1.0

    def test_cr_08_a_non_numeric_weight_is_refused(self):
        """CR-08"""
        thing = self._thing()
        with self.assertRaises(AttributeError):
            thing.weight = "heavy"

    def test_cr_09_none_is_refused(self):
        """CR-09"""
        thing = self._thing()
        with self.assertRaises(AttributeError):
            thing.weight = None

    def test_cr_10_a_boolean_weight_is_refused(self):
        """CR-10"""
        thing = self._thing()
        with self.assertRaises(AttributeError):
            thing.weight = True
        with self.assertRaises(AttributeError):
            thing.weight = False

    def test_cr_11_a_weight_set_through_db_bypasses_validation(self):
        """CR-11"""
        thing = self._thing()
        thing.db.weight = -5.0
        self.assertEqual(thing.weight, -5.0)


class CarryingTests(DjangoTestCase):
    """CA — rebuilding a carrier's weight from its contents."""

    def _carrier(self):
        """Create one carrier. Not a test. See ``_thing`` on ``nohome``."""
        from evennia import create_object
        from tests.game_typeclasses import Carrier

        return create_object(Carrier, key="carrier", nohome=True)

    def _carried(self, carrier, weight):
        """Put one carriable object of the given weight into a carrier."""
        from evennia import create_object
        from tests.game_typeclasses import CarriableThing

        thing = create_object(
            CarriableThing, key="thing", location=carrier, nohome=True
        )
        thing.weight = weight
        return thing

    def test_ca_01_empty_contents_weighs_zero(self):
        """CA-01"""
        carrier = self._carrier()
        # Seeded non-zero, or a method that did nothing would pass this on the
        # default alone.
        carrier.items_weight = 9.0
        carrier._recalculate_item_weight()
        self.assertEqual(carrier.items_weight, 0.0)

    def test_ca_02_one_object_gives_its_own_weight(self):
        """CA-02"""
        carrier = self._carrier()
        self._carried(carrier, 2.5)
        carrier._recalculate_item_weight()
        self.assertEqual(carrier.items_weight, 2.5)

    def test_ca_03_several_objects_give_their_sum(self):
        """CA-03"""
        carrier = self._carrier()
        for weight in (1.0, 2.5, 0.5):
            self._carried(carrier, weight)
        carrier._recalculate_item_weight()
        self.assertEqual(carrier.items_weight, 4.0)

    def test_ca_04_an_excluded_object_is_left_out(self):
        """CA-04"""
        carrier = self._carrier()
        self._carried(carrier, 1.0)
        leaving = self._carried(carrier, 2.0)
        carrier._recalculate_item_weight(exclude=leaving)
        self.assertEqual(carrier.items_weight, 1.0)

    def test_ca_05_recalculating_twice_gives_the_same_answer(self):
        """CA-05"""
        carrier = self._carrier()
        self._carried(carrier, 3.0)
        carrier._recalculate_item_weight()
        carrier._recalculate_item_weight()
        self.assertEqual(carrier.items_weight, 3.0)

    def test_ca_06_a_deleted_object_drops_out(self):
        """CA-06"""
        carrier = self._carrier()
        thing = self._carried(carrier, 3.0)
        carrier._recalculate_item_weight()
        thing.delete()
        carrier._recalculate_item_weight()
        self.assertEqual(carrier.items_weight, 0.0)


class HookTests(DjangoTestCase):
    """PR, RC, LV, IN — the overrides that keep the total current."""

    def _make(self, typeclass, **kwargs):
        """Create one object. Not a test. See CarriableTests._thing on nohome."""
        from evennia import create_object

        return create_object(typeclass, key=typeclass.__name__, nohome=True, **kwargs)

    def _carrier(self, typeclass=None):
        from tests.game_typeclasses import Carrier

        return self._make(typeclass or Carrier)

    def _loose(self, weight):
        """A carriable object of the given weight, in no location."""
        from tests.game_typeclasses import CarriableThing

        thing = self._make(CarriableThing)
        thing.weight = weight
        return thing

    # --- PR: at_pre_object_receive ---------------------------------------

    def test_pr_01_an_object_without_the_mixin_is_refused(self):
        """PR-01"""
        from tests.game_typeclasses import Nowhere

        carrier = self._carrier()
        stone = self._make(Nowhere)
        self.assertFalse(stone.move_to(carrier))
        self.assertNotIn(stone, carrier.contents)

    def test_pr_02_an_object_with_the_mixin_is_accepted(self):
        """PR-02"""
        carrier = self._carrier()
        thing = self._loose(1.0)
        self.assertTrue(thing.move_to(carrier))
        self.assertIn(thing, carrier.contents)

    def test_pr_03_a_refusal_from_super_is_passed_on(self):
        """PR-03"""
        from tests.game_typeclasses import RefusingCarrier

        carrier = self._carrier(RefusingCarrier)
        thing = self._loose(1.0)
        self.assertFalse(thing.move_to(carrier))
        self.assertNotIn(thing, carrier.contents)

    def test_pr_04_a_refused_arrival_is_logged(self):
        """PR-04"""
        from tests.game_typeclasses import Nowhere

        carrier = self._carrier()
        stone = self._make(Nowhere)
        with mock.patch("evennia_equipment.carrying.equipment_log") as logged:
            stone.move_to(carrier)
        self.assertTrue(logged.called)

    # --- RC: at_object_receive -------------------------------------------

    def test_rc_01_an_object_moved_in_is_counted(self):
        """RC-01"""
        carrier = self._carrier()
        self._loose(2.5).move_to(carrier)
        self.assertEqual(carrier.items_weight, 2.5)

    def test_rc_02_an_object_created_in_the_carrier_is_counted(self):
        """RC-02"""
        from tests.game_typeclasses import CarriableThing

        carrier = self._carrier()
        self._make(CarriableThing, location=carrier).weight = 1.5
        carrier._recalculate_item_weight()
        self.assertEqual(carrier.items_weight, 1.5)

    def test_rc_03_receive_calls_super(self):
        """RC-03"""
        from tests.game_typeclasses import RecordingCarrier

        carrier = self._carrier(RecordingCarrier)
        self._loose(1.0).move_to(carrier)
        self.assertTrue(carrier.ndb.receive_super_ran)

    # --- LV: at_object_leave ---------------------------------------------

    def test_lv_01_an_object_moved_out_stops_being_counted(self):
        """LV-01"""
        from tests.game_typeclasses import Nowhere

        carrier = self._carrier()
        thing = self._loose(2.0)
        thing.move_to(carrier)
        thing.move_to(self._make(Nowhere))
        self.assertEqual(carrier.items_weight, 0.0)

    def test_lv_02_leave_calls_super(self):
        """LV-02"""
        from tests.game_typeclasses import Nowhere, RecordingCarrier

        carrier = self._carrier(RecordingCarrier)
        thing = self._loose(1.0)
        thing.move_to(carrier)
        thing.move_to(self._make(Nowhere))
        self.assertTrue(carrier.ndb.leave_super_ran)

    # --- IN: at_init ------------------------------------------------------

    def test_in_01_a_stale_total_is_corrected_on_load(self):
        """IN-01"""
        carrier = self._carrier()
        carrier.items_weight = 9.0
        carrier.at_init()
        self.assertEqual(carrier.items_weight, 0.0)

    def test_in_02_an_unsaved_carrier_does_not_raise(self):
        """IN-02"""
        from tests.game_typeclasses import Carrier

        self.assertIsNone(Carrier().at_init())

    def test_in_03_init_calls_super(self):
        """IN-03"""
        from tests.game_typeclasses import RecordingCarrier

        carrier = self._carrier(RecordingCarrier)
        carrier.at_init()
        self.assertTrue(carrier.ndb.init_super_ran)


class TotalAndCapacityTests(DjangoTestCase):
    """TW, CP — the carried total, capacity, and the queries over them."""

    def _carrier(self, typeclass=None, carrying=0.0):
        """A carrier holding one object of the given weight. Not a test."""
        from evennia import create_object
        from tests.game_typeclasses import CarriableThing, Carrier

        carrier = create_object(typeclass or Carrier, key="carrier", nohome=True)
        if carrying:
            # Weighed before it arrives, then moved in. Setting the weight of
            # something already held does not rebuild the total — see the open
            # decision on weight changing in place.
            thing = create_object(CarriableThing, key="thing", nohome=True)
            thing.weight = carrying
            thing.move_to(carrier)
        return carrier

    def _purse(self, carrying=0.0):
        from tests.game_typeclasses import PurseCarrier

        return self._carrier(PurseCarrier, carrying=carrying)

    # --- TW: the carried total -------------------------------------------

    def test_tw_01_extra_weight_defaults_to_zero(self):
        """TW-01"""
        self.assertEqual(self._carrier().extra_weight(), 0.0)

    def test_tw_02_the_total_is_items_plus_extra(self):
        """TW-02"""
        carrier = self._purse(carrying=2.0)
        carrier.ndb.coin_weight = 0.5
        self.assertEqual(carrier.current_weight_carried, 2.5)

    def test_tw_03_overriding_extra_weight_changes_the_total(self):
        """TW-03"""
        plain = self._carrier(carrying=2.0)
        purse = self._purse(carrying=2.0)
        purse.ndb.coin_weight = 3.0
        self.assertEqual(plain.current_weight_carried, 2.0)
        self.assertEqual(purse.current_weight_carried, 5.0)

    def test_tw_04_the_total_reflects_a_changed_extra_weight_immediately(self):
        """TW-04"""
        carrier = self._purse(carrying=1.0)
        carrier.ndb.coin_weight = 1.0
        self.assertEqual(carrier.current_weight_carried, 2.0)
        # Nothing is told to update — a cached total would still read 2.0.
        carrier.ndb.coin_weight = 4.0
        self.assertEqual(carrier.current_weight_carried, 5.0)

    # --- CP: capacity -----------------------------------------------------

    def test_cp_01_capacity_is_unlimited_by_default(self):
        """CP-01"""
        carrier = self._carrier(carrying=1000.0)
        self.assertTrue(carrier.can_carry(10_000.0))
        self.assertFalse(carrier.is_encumbered)

    def test_cp_02_remaining_capacity_is_infinite_by_default(self):
        """CP-02"""
        self.assertEqual(self._carrier().get_remaining_capacity(), float("inf"))

    def test_cp_03_a_subclass_can_override_the_capacity_default(self):
        """CP-03"""
        from tests.game_typeclasses import BulkyCarrier

        self.assertEqual(self._carrier(BulkyCarrier).max_carrying_capacity, 20.0)

    def test_cp_04_a_negative_capacity_is_refused(self):
        """CP-04"""
        carrier = self._carrier()
        with self.assertRaises(AttributeError):
            carrier.max_carrying_capacity = -1.0

    def test_cp_05_extra_capacity_defaults_to_zero(self):
        """CP-05"""
        self.assertEqual(self._carrier().extra_capacity(), 0.0)

    def test_cp_06_effective_capacity_is_stored_plus_extra(self):
        """CP-06"""
        carrier = self._purse()
        carrier.max_carrying_capacity = 10.0
        carrier.ndb.strength_bonus = 5.0
        self.assertEqual(carrier.effective_capacity, 15.0)

    def test_cp_07_overriding_extra_capacity_changes_the_effective_capacity(self):
        """CP-07"""
        carrier = self._purse()
        carrier.max_carrying_capacity = 10.0
        self.assertEqual(carrier.effective_capacity, 10.0)
        # A potion lands; nothing recalculates anything.
        carrier.ndb.strength_bonus = 8.0
        self.assertEqual(carrier.effective_capacity, 18.0)

    def test_cp_08_remaining_capacity_is_effective_less_the_total(self):
        """CP-08"""
        carrier = self._carrier(carrying=3.0)
        carrier.max_carrying_capacity = 10.0
        self.assertEqual(carrier.get_remaining_capacity(), 7.0)

    def test_cp_09_remaining_capacity_does_not_go_below_zero(self):
        """CP-09"""
        carrier = self._carrier(carrying=8.0)
        carrier.max_carrying_capacity = 3.0
        self.assertEqual(carrier.get_remaining_capacity(), 0.0)

    def test_cp_10_can_carry_is_true_when_it_fits(self):
        """CP-10"""
        carrier = self._carrier(carrying=3.0)
        carrier.max_carrying_capacity = 10.0
        self.assertTrue(carrier.can_carry(7.0))

    def test_cp_11_can_carry_is_false_when_it_does_not(self):
        """CP-11"""
        carrier = self._carrier(carrying=3.0)
        carrier.max_carrying_capacity = 10.0
        self.assertFalse(carrier.can_carry(7.5))

    def test_cp_12_is_encumbered_is_false_at_exactly_capacity(self):
        """CP-12"""
        carrier = self._carrier(carrying=10.0)
        carrier.max_carrying_capacity = 10.0
        self.assertFalse(carrier.is_encumbered)

    def test_cp_13_is_encumbered_is_true_above_capacity(self):
        """CP-13"""
        carrier = self._carrier(carrying=10.5)
        carrier.max_carrying_capacity = 10.0
        self.assertTrue(carrier.is_encumbered)


class WeightChangeTests(DjangoTestCase):
    """EW, WC — what an object contributes, and changing it while held."""

    def _make(self, typeclass, **kwargs):
        """Create one object. Not a test."""
        from evennia import create_object

        return create_object(typeclass, key=typeclass.__name__, nohome=True, **kwargs)

    def _carrier(self):
        from tests.game_typeclasses import Carrier

        return self._make(Carrier)

    # --- EW: effective_weight --------------------------------------------

    def test_ew_01_effective_weight_is_the_objects_own_weight(self):
        """EW-01"""
        from tests.game_typeclasses import CarriableThing

        thing = self._make(CarriableThing)
        thing.weight = 2.5
        self.assertEqual(thing.effective_weight, 2.5)

    def test_ew_02_the_total_is_built_from_effective_weight(self):
        """EW-02"""
        from tests.game_typeclasses import PaddedThing

        carrier = self._carrier()
        padded = self._make(PaddedThing)
        padded.weight = 2.0
        padded.move_to(carrier)
        # 2.0 of its own, plus the 1.0 its effective weight adds.
        self.assertEqual(carrier.items_weight, 3.0)

    # --- WC: at_weight_changed -------------------------------------------

    def test_wc_01_changing_a_held_objects_weight_rebuilds_the_total(self):
        """WC-01"""
        from tests.game_typeclasses import CarriableThing

        carrier = self._carrier()
        thing = self._make(CarriableThing)
        thing.weight = 2.0
        thing.move_to(carrier)
        self.assertEqual(carrier.items_weight, 2.0)
        thing.weight = 5.0
        self.assertEqual(carrier.items_weight, 5.0)

    def test_wc_02_changing_an_unheld_objects_weight_is_harmless(self):
        """WC-02"""
        from tests.game_typeclasses import CarriableThing

        thing = self._make(CarriableThing)
        thing.weight = 4.0
        self.assertEqual(thing.weight, 4.0)

    def test_wc_03_an_object_held_by_a_non_carrier_is_harmless(self):
        """WC-03"""
        from tests.game_typeclasses import CarriableThing, Nowhere

        thing = self._make(CarriableThing, location=self._make(Nowhere))
        thing.weight = 4.0
        self.assertEqual(thing.weight, 4.0)

    def test_wc_04_a_consumer_override_still_gets_the_rebuild(self):
        """WC-04"""
        from tests.game_typeclasses import NoisyThing

        carrier = self._carrier()
        thing = self._make(NoisyThing)
        thing.move_to(carrier)
        thing.weight = 6.0
        self.assertTrue(thing.ndb.weight_change_seen)
        self.assertEqual(carrier.items_weight, 6.0)


class ContainerTests(DjangoTestCase):
    """CN — an object that is carried and carrying at once."""

    def _make(self, typeclass, **kwargs):
        """Create one object. Not a test."""
        from evennia import create_object

        return create_object(typeclass, key=typeclass.__name__, nohome=True, **kwargs)

    def _carrier(self):
        from tests.game_typeclasses import Carrier

        return self._make(Carrier)

    def _container(self, typeclass=None, own_weight=1.0):
        from tests.game_typeclasses import Container

        container = self._make(typeclass or Container)
        container.weight = own_weight
        return container

    def _thing(self, weight, location=None):
        from tests.game_typeclasses import CarriableThing

        thing = self._make(CarriableThing)
        thing.weight = weight
        if location:
            thing.move_to(location)
        return thing

    # --- what a container contributes ------------------------------------

    def test_cn_01_an_empty_containers_effective_weight_is_its_own(self):
        """CN-01"""
        self.assertEqual(self._container(own_weight=1.5).effective_weight, 1.5)

    def test_cn_02_a_loaded_containers_effective_weight_includes_contents(self):
        """CN-02"""
        container = self._container(own_weight=1.0)
        self._thing(2.0, location=container)
        self.assertEqual(container.effective_weight, 3.0)

    def test_cn_03_a_carrier_counts_a_containers_contents_through_it(self):
        """CN-03"""
        carrier = self._carrier()
        container = self._container(own_weight=1.0)
        self._thing(2.0, location=container)
        container.move_to(carrier)
        self.assertEqual(carrier.items_weight, 3.0)

    def test_cn_12_a_containers_extra_weight_counts_toward_what_it_contributes(self):
        """CN-12"""
        from tests.game_typeclasses import PurseContainer

        container = self._container(PurseContainer, own_weight=1.0)
        container.ndb.coin_weight = 0.5
        self.assertEqual(container.effective_weight, 1.5)

    # --- propagation -------------------------------------------------------

    def test_cn_04_adding_to_a_held_container_updates_the_carrier(self):
        """CN-04"""
        carrier = self._carrier()
        container = self._container(own_weight=1.0)
        container.move_to(carrier)
        self.assertEqual(carrier.items_weight, 1.0)
        self._thing(2.0, location=container)
        self.assertEqual(carrier.items_weight, 3.0)

    def test_cn_05_removing_from_a_held_container_updates_the_carrier(self):
        """CN-05"""
        from tests.game_typeclasses import Nowhere

        carrier = self._carrier()
        container = self._container(own_weight=1.0)
        thing = self._thing(2.0, location=container)
        container.move_to(carrier)
        self.assertEqual(carrier.items_weight, 3.0)
        thing.move_to(self._make(Nowhere))
        self.assertEqual(carrier.items_weight, 1.0)

    def test_cn_06_changing_a_weight_inside_a_container_updates_the_carrier(self):
        """CN-06"""
        carrier = self._carrier()
        container = self._container(own_weight=1.0)
        thing = self._thing(2.0, location=container)
        container.move_to(carrier)
        self.assertEqual(carrier.items_weight, 3.0)
        thing.weight = 5.0
        self.assertEqual(carrier.items_weight, 6.0)

    def test_cn_07_two_levels_of_nesting_propagate_to_the_top(self):
        """CN-07"""
        carrier = self._carrier()
        outer = self._container(own_weight=1.0)
        inner = self._container(own_weight=1.0)
        inner.move_to(outer)
        outer.move_to(carrier)
        self.assertEqual(carrier.items_weight, 2.0)
        self._thing(4.0, location=inner)
        self.assertEqual(carrier.items_weight, 6.0)

    def test_cn_08_propagation_stops_at_a_holder_that_does_not_carry(self):
        """CN-08"""
        from tests.game_typeclasses import Nowhere

        container = self._container(own_weight=1.0)
        container.move_to(self._make(Nowhere))
        self._thing(2.0, location=container)
        self.assertEqual(container.effective_weight, 3.0)

    def test_cn_09_a_containers_own_weight_change_updates_the_carrier(self):
        """CN-09"""
        carrier = self._carrier()
        container = self._container(own_weight=1.0)
        container.move_to(carrier)
        self.assertEqual(carrier.items_weight, 1.0)
        container.weight = 4.0
        self.assertEqual(carrier.items_weight, 4.0)

    # --- composition, and the risk ----------------------------------------

    def test_cn_10_a_container_refuses_what_cannot_be_carried(self):
        """CN-10"""
        from tests.game_typeclasses import Nowhere

        container = self._container()
        stone = self._make(Nowhere)
        self.assertFalse(stone.move_to(container))
        self.assertNotIn(stone, container.contents)

    def test_cn_13_a_subclass_may_contribute_only_its_own_weight(self):
        """CN-13"""
        from tests.game_typeclasses import PanniersContainer

        carrier = self._carrier()
        panniers = self._container(PanniersContainer, own_weight=1.0)
        self._thing(9.0, location=panniers)
        panniers.move_to(carrier)
        self.assertEqual(carrier.items_weight, 1.0)

    def test_cn_14_loading_a_container_into_memory_does_not_raise(self):
        """CN-14"""
        from tests.game_typeclasses import Container

        carrier = self._carrier()
        container = self._container(own_weight=1.0)
        self._thing(2.0, location=container)
        container.move_to(carrier)
        container.at_init()
        self.assertIsNone(Container().at_init())
