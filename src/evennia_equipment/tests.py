# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for evennia-equipment. Run via ``python runtests.py``.

Every test carries its case ID from docs/test-plan.md as its docstring, so
the coverage trail reads in both directions.
"""

from contextlib import contextmanager
from unittest import TestCase, mock

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase as DjangoTestCase
from django.test import override_settings

import evennia_equipment
from evennia_equipment.config import (
    PROBLEM_PREFIX,
    SETTING_IDENTITY,
    SETTING_WEARSLOTS,
    check_settings,
    get_identity_attribute,
    valid_slot_names,
)
from evennia_equipment.log import equipment_log
from evennia_equipment.targeting import f_identity_in, f_worn_by
from evennia_targeting.testing import validate_factory

_ENUMS = "tests.slot_enums"


@contextmanager
def _slots(path):
    """Point EQUIPMENT_WEARSLOTS at ``path`` for the block.

    Simulates a restart with a different slot enum, which is the only way the
    slots ever change. ``valid_slot_names`` holds its answer for the life of
    the process, so clearing the cache is what makes this a faithful stand-in
    rather than a workaround — and it is cleared on the way out too, or the
    swapped enum would outlive the block.
    """
    valid_slot_names.cache_clear()
    try:
        with override_settings(**{SETTING_WEARSLOTS: path}):
            yield
    finally:
        valid_slot_names.cache_clear()


class ScaffoldTests(TestCase):
    """SC — the library is installed and the runner reaches it."""

    def test_sc_01_the_package_is_importable_and_versioned(self):
        """SC-01"""
        self.assertTrue(evennia_equipment.__version__)

    def test_sc_02_the_log_shim_is_a_no_op_outside_evennia(self):
        """SC-02"""
        self.assertIsNone(equipment_log("scaffold check"))


class ConfigTests(TestCase):
    """CF — the declared slot enum, and the boot check that refuses a bad one."""

    def _refusal(self, value):
        """Run the check against one setting value and return the message."""
        with _slots(value):
            with self.assertRaises(ImproperlyConfigured) as caught:
                check_settings()
        return str(caught.exception)

    def test_cf_01_a_missing_setting_is_refused(self):
        """CF-01"""
        self.assertIn(SETTING_WEARSLOTS, self._refusal(None))

    def test_cf_02_an_unresolvable_path_is_refused_with_the_cause(self):
        """CF-02"""
        with _slots("tests.no_such_module.WearSlot"):
            with self.assertRaises(ImproperlyConfigured) as caught:
                check_settings()
        self.assertIsNotNone(caught.exception.__cause__)

    def test_cf_03_something_that_is_not_an_enum_is_refused(self):
        """CF-03"""
        self.assertIn(SETTING_WEARSLOTS, self._refusal(f"{_ENUMS}.NOT_AN_ENUM"))

    def test_cf_06_a_non_string_member_value_is_refused(self):
        """CF-06"""
        self.assertIn("BODY", self._refusal(f"{_ENUMS}.NonStringValue"))

    def test_cf_07_a_repeated_member_value_is_refused(self):
        """CF-07"""
        self.assertIn("SKULL", self._refusal(f"{_ENUMS}.RepeatedValue"))

    def test_cf_09_a_valid_configuration_boots(self):
        """CF-09"""
        with _slots(f"{_ENUMS}.WearSlot"):
            self.assertIsNone(check_settings())

    def test_cf_10_the_accessor_returns_the_enums_values(self):
        """CF-10"""
        with _slots(f"{_ENUMS}.WearSlot"):
            names = valid_slot_names()
        self.assertIn("HEAD", names)
        self.assertIn("DOG_NECK", names)

    def test_cf_11_an_enum_with_no_members_is_refused(self):
        """CF-11"""
        self.assertIn(SETTING_WEARSLOTS, self._refusal(f"{_ENUMS}.NoMembers"))

    def _identity_refusal(self, value):
        """Run the check with a bad identity attribute, enum otherwise fine."""
        with _slots(f"{_ENUMS}.WearSlot"), override_settings(
            **{SETTING_IDENTITY: value}
        ):
            with self.assertRaises(ImproperlyConfigured) as caught:
                check_settings()
        return str(caught.exception)

    def test_cf_14_a_missing_identity_attribute_is_refused(self):
        """CF-14"""
        self.assertIn(SETTING_IDENTITY, self._identity_refusal(None))

    def test_cf_15_a_non_string_identity_attribute_is_refused(self):
        """CF-15"""
        self.assertIn(SETTING_IDENTITY, self._identity_refusal(7))

    def test_cf_16_an_empty_identity_attribute_is_refused(self):
        """CF-16"""
        self.assertIn(SETTING_IDENTITY, self._identity_refusal(""))

    def test_cf_17_both_settings_wrong_are_reported_at_once(self):
        """CF-17"""
        with _slots(f"{_ENUMS}.NoMembers"), override_settings(
            **{SETTING_IDENTITY: None}
        ):
            with self.assertRaises(ImproperlyConfigured) as caught:
                check_settings()
        self.assertEqual(str(caught.exception).count(PROBLEM_PREFIX), 2)

    def test_cf_18_the_accessor_returns_the_attribute_name(self):
        """CF-18"""
        with override_settings(**{SETTING_IDENTITY: "token_id"}):
            self.assertEqual(get_identity_attribute(), "token_id")


class WearableTests(DjangoTestCase):
    """WR — an item's slot declaration, and what may be stored in it."""

    def _item(self, typeclass=None):
        """Create one wearable item. Not a test."""
        from evennia import create_object
        from tests.game_typeclasses import WearableThing

        return create_object(typeclass or WearableThing, key="item", nohome=True)

    def _refused(self, value):
        """Assert a declaration is refused, and return the message."""
        item = self._item()
        with self.assertRaises(AttributeError) as caught:
            item.wearslot = value
        return str(caught.exception)

    def test_wr_01_a_canonical_declaration_is_accepted(self):
        """WR-01"""
        item = self._item()
        item.wearslot = [["LEFT_HAND"], ["RIGHT_HAND"]]
        self.assertEqual(item.wearslot, [["LEFT_HAND"], ["RIGHT_HAND"]])

    def test_wr_02_a_bare_string_is_refused(self):
        """WR-02"""
        self._refused("HEAD")

    def test_wr_03_a_flat_list_is_refused(self):
        """WR-03"""
        self._refused(["LEFT_HAND", "RIGHT_HAND"])

    def test_wr_04_a_group_holding_a_non_string_is_refused(self):
        """WR-04"""
        self._refused([["HEAD", 7]])

    def test_wr_05_a_declaration_with_no_groups_is_refused(self):
        """WR-05"""
        self._refused([])

    def test_wr_06_a_group_with_no_slots_is_refused(self):
        """WR-06"""
        self._refused([[]])

    def test_wr_07_a_slot_the_enum_does_not_hold_is_refused(self):
        """WR-07"""
        self.assertIn("HAED", self._refused([["HAED"]]))

    def test_wr_08_a_slot_in_the_enum_is_accepted(self):
        """WR-08"""
        item = self._item()
        item.wearslot = [["DOG_NECK"]]
        self.assertEqual(item.wearslot, [["DOG_NECK"]])

    def test_wr_09_a_class_default_is_validated_on_first_read(self):
        """WR-09"""
        from tests.game_typeclasses import Helm, MistypedHelm

        self.assertEqual(self._item(Helm).wearslot, [["HEAD"]])
        with self.assertRaises(AttributeError):
            self._item(MistypedHelm).wearslot

    def test_wr_10_a_slot_repeated_in_one_group_is_refused(self):
        """WR-10"""
        self.assertIn("HEAD", self._refused([["HEAD", "HEAD"]]))

    def test_wr_11_a_declaration_set_through_db_bypasses_validation(self):
        """WR-11"""
        item = self._item()
        item.db.wearslot = "HEAD"
        self.assertEqual(item.wearslot, "HEAD")


class WearslotsTests(DjangoTestCase):
    """WS — a wearer's slots, from the body plan its subclass declares."""

    def _wearer(self, typeclass=None):
        """Create one wearer. Not a test."""
        from evennia import create_object
        from tests.game_typeclasses import Humanoid

        return create_object(typeclass or Humanoid, key="wearer", nohome=True)

    def _subclass(self, slots):
        """Declare a wearslots subclass with these body_slots.

        Declared inside a test body because the ones that are wrong cannot
        exist at module scope — the module would not import.
        """
        from evennia_equipment.wearslots import EquipmentWearslotsMixin

        return type("Declared", (EquipmentWearslotsMixin,), {"body_slots": slots})

    def test_ws_01_slots_come_from_body_slots(self):
        """WS-01"""
        self.assertEqual(
            set(self._wearer().worn_items),
            {"HEAD", "BODY", "LEFT_HAND", "RIGHT_HAND"},
        )

    def test_ws_02_every_slot_starts_empty(self):
        """WS-02"""
        self.assertTrue(all(item is None for item in self._wearer().worn_items.values()))

    def test_ws_03_slots_keep_the_declared_order(self):
        """WS-03"""
        self.assertEqual(
            list(self._wearer().worn_items),
            ["HEAD", "BODY", "LEFT_HAND", "RIGHT_HAND"],
        )

    def test_ws_04_different_body_slots_give_different_slots(self):
        """WS-04"""
        from tests.game_typeclasses import Dog

        self.assertEqual(set(self._wearer(Dog).worn_items), {"DOG_NECK", "DOG_BODY"})

    def test_ws_11_an_empty_dictionary_is_populated_on_load(self):
        """WS-11"""
        wearer = self._wearer()
        # An object that predates the mixin: at_object_creation has already
        # run for it and will not run again.
        wearer.db.worn_items = None
        wearer.at_init()
        self.assertEqual(
            set(wearer.worn_items), {"HEAD", "BODY", "LEFT_HAND", "RIGHT_HAND"}
        )

    def test_ws_12_a_slot_added_to_body_slots_is_added_on_load(self):
        """WS-12"""
        from tests.game_typeclasses import Humanoid
        from tests.slot_enums import WearSlot

        wearer = self._wearer()
        self.assertNotIn("DOG_NECK", wearer.worn_items)
        with mock.patch.object(
            Humanoid, "body_slots", Humanoid.body_slots + (WearSlot.DOG_NECK,)
        ):
            wearer.at_init()
            self.assertIn("DOG_NECK", wearer.worn_items)

    def test_ws_13_a_slot_removed_from_body_slots_is_removed_on_load(self):
        """WS-13"""
        from tests.game_typeclasses import Humanoid
        from tests.slot_enums import WearSlot

        wearer = self._wearer()
        with mock.patch.object(Humanoid, "body_slots", (WearSlot.HEAD,)):
            wearer.at_init()
            self.assertEqual(set(wearer.worn_items), {"HEAD"})

    def test_ws_14_an_item_in_a_removed_slot_stops_being_worn(self):
        """WS-14"""
        from evennia import create_object
        from tests.game_typeclasses import Helmet, Humanoid
        from tests.slot_enums import WearSlot

        wearer = self._wearer()
        helmet = create_object(Helmet, key="helmet", location=wearer, nohome=True)
        wearer.wear(helmet)
        with mock.patch.object(Humanoid, "body_slots", (WearSlot.BODY,)):
            wearer.at_init()
        self.assertFalse(wearer.is_worn(helmet))
        self.assertIn(helmet, wearer.contents)

    def test_ws_15_a_slot_the_enum_does_not_hold_is_refused_at_import(self):
        """WS-15"""
        from enum import Enum

        class Rogue(Enum):
            HAED = "HAED"

        with self.assertRaises(AttributeError) as caught:
            self._subclass((Rogue.HAED,))
        self.assertIn("HAED", str(caught.exception))

    def test_ws_16_reconciliation_leaves_existing_assignments_alone(self):
        """WS-16"""
        from evennia import create_object
        from tests.game_typeclasses import Helmet, Humanoid
        from tests.slot_enums import WearSlot

        wearer = self._wearer()
        helmet = create_object(Helmet, key="helmet", location=wearer, nohome=True)
        wearer.wear(helmet)
        with mock.patch.object(
            Humanoid, "body_slots", Humanoid.body_slots + (WearSlot.DOG_NECK,)
        ):
            wearer.at_init()
        self.assertIs(wearer.worn_items["HEAD"], helmet)

    def test_ws_17_a_subclass_declaring_no_slots_is_refused(self):
        """WS-17"""
        with self.assertRaises(AttributeError) as caught:
            self._subclass(())
        self.assertIn("body_slots", str(caught.exception))

    def test_ws_18_a_plain_string_instead_of_an_enum_member_is_refused(self):
        """WS-18"""
        with self.assertRaises(AttributeError) as caught:
            self._subclass(("HEAD",))
        self.assertIn("HEAD", str(caught.exception))

    def test_ws_19_a_repeated_slot_is_refused(self):
        """WS-19"""
        from tests.slot_enums import WearSlot

        with self.assertRaises(AttributeError) as caught:
            self._subclass((WearSlot.HEAD, WearSlot.HEAD))
        self.assertIn("HEAD", str(caught.exception))


class WearTests(DjangoTestCase):
    """WE — choosing a group of slots and filling it."""

    def _wearer(self, typeclass=None):
        """Create one wearer. Not a test."""
        from evennia import create_object
        from tests.game_typeclasses import Humanoid

        return create_object(typeclass or Humanoid, key="wearer", nohome=True)

    def _held(self, wearer, typeclass):
        """Create one wearable item already in the wearer's contents."""
        from evennia import create_object

        return create_object(
            typeclass, key=typeclass.__name__, location=wearer, nohome=True
        )

    def test_we_01_a_single_slot_item_fills_that_slot(self):
        """WE-01"""
        from tests.game_typeclasses import Helmet

        wearer = self._wearer()
        helmet = self._held(wearer, Helmet)
        worn, _ = wearer.wear(helmet)
        self.assertTrue(worn)
        self.assertIs(wearer.worn_items["HEAD"], helmet)

    def test_we_02_a_multi_slot_item_fills_every_slot_in_its_group(self):
        """WE-02"""
        from tests.game_typeclasses import Greatsword

        wearer = self._wearer()
        sword = self._held(wearer, Greatsword)
        wearer.wear(sword)
        self.assertIs(wearer.worn_items["LEFT_HAND"], sword)
        self.assertIs(wearer.worn_items["RIGHT_HAND"], sword)

    def test_we_03_the_first_free_group_is_chosen(self):
        """WE-03"""
        from tests.game_typeclasses import Ring

        wearer = self._wearer()
        ring = self._held(wearer, Ring)
        wearer.wear(ring)
        self.assertIs(wearer.worn_items["LEFT_HAND"], ring)
        self.assertIsNone(wearer.worn_items["RIGHT_HAND"])

    def test_we_04_a_later_group_is_chosen_when_the_first_is_taken(self):
        """WE-04"""
        from tests.game_typeclasses import Ring

        wearer = self._wearer()
        first, second = self._held(wearer, Ring), self._held(wearer, Ring)
        wearer.wear(first)
        wearer.wear(second)
        self.assertIs(wearer.worn_items["LEFT_HAND"], first)
        self.assertIs(wearer.worn_items["RIGHT_HAND"], second)

    def test_we_05_a_partly_blocked_group_is_not_partly_filled(self):
        """WE-05"""
        from tests.game_typeclasses import Greatsword, Ring

        wearer = self._wearer()
        ring = self._held(wearer, Ring)
        sword = self._held(wearer, Greatsword)
        wearer.wear(ring)
        worn, _ = wearer.wear(sword)
        self.assertFalse(worn)
        self.assertIs(wearer.worn_items["LEFT_HAND"], ring)
        self.assertIsNone(wearer.worn_items["RIGHT_HAND"])

    def test_we_06_a_group_naming_a_missing_slot_is_skipped(self):
        """WE-06"""
        from tests.game_typeclasses import Collar

        wearer = self._wearer()
        worn, _ = wearer.wear(self._held(wearer, Collar))
        self.assertFalse(worn)

    def test_we_07_an_item_not_in_contents_is_refused(self):
        """WE-07"""
        from evennia import create_object
        from tests.game_typeclasses import Helmet

        wearer = self._wearer()
        loose = create_object(Helmet, key="helmet", nohome=True)
        worn, _ = wearer.wear(loose)
        self.assertFalse(worn)
        self.assertIsNone(wearer.worn_items["HEAD"])

    def test_we_08_an_item_already_worn_is_refused(self):
        """WE-08"""
        from tests.game_typeclasses import Helmet

        wearer = self._wearer()
        helmet = self._held(wearer, Helmet)
        wearer.wear(helmet)
        worn, _ = wearer.wear(helmet)
        self.assertFalse(worn)

    def test_we_09_an_item_declaring_no_slots_is_refused(self):
        """WE-09"""
        from tests.game_typeclasses import WearableThing

        wearer = self._wearer()
        worn, _ = wearer.wear(self._held(wearer, WearableThing))
        self.assertFalse(worn)

    def test_we_10_wearing_is_refused_when_no_group_is_usable(self):
        """WE-10"""
        from tests.game_typeclasses import Helmet

        wearer = self._wearer()
        first, second = self._held(wearer, Helmet), self._held(wearer, Helmet)
        wearer.wear(first)
        worn, _ = wearer.wear(second)
        self.assertFalse(worn)
        self.assertIs(wearer.worn_items["HEAD"], first)

    def test_we_11_wearing_does_not_move_the_item(self):
        """WE-11"""
        from tests.game_typeclasses import Helmet

        wearer = self._wearer()
        helmet = self._held(wearer, Helmet)
        wearer.wear(helmet)
        self.assertIn(helmet, wearer.contents)

    def test_we_12_wearing_does_not_change_the_carried_weight(self):
        """WE-12"""
        from tests.game_typeclasses import Helmet

        wearer = self._wearer()
        helmet = self._held(wearer, Helmet)
        helmet.weight = 2.0
        before = wearer.items_weight
        wearer.wear(helmet)
        self.assertEqual(wearer.items_weight, before)

    def test_we_13_both_outcomes_return_a_message(self):
        """WE-13"""
        from tests.game_typeclasses import Helmet

        wearer = self._wearer()
        helmet = self._held(wearer, Helmet)
        _, said = wearer.wear(helmet)
        self.assertTrue(said)
        _, refused = wearer.wear(helmet)
        self.assertTrue(refused)

    # --- resolving a string ------------------------------------------------

    def _named(self, wearer, typeclass, key):
        """Create a wearable in contents under a key of the test's choosing.

        The `_held` helper keys everything after its typeclass, which is fine
        while items are told apart by type. These cases tell them apart by
        name, so the name is the thing under test.
        """
        from evennia import create_object

        return create_object(typeclass, key=key, location=wearer, nohome=True)

    def test_we_14_a_string_naming_a_carried_item_wears_it(self):
        """WE-14"""
        from tests.game_typeclasses import Helmet

        wearer = self._wearer()
        helmet = self._named(wearer, Helmet, "iron helmet")
        worn, _ = wearer.wear("iron helmet")
        self.assertTrue(worn)
        self.assertIs(wearer.worn_items["HEAD"], helmet)

    def test_we_15_matching_ignores_case(self):
        """WE-15"""
        from tests.game_typeclasses import Helmet

        wearer = self._wearer()
        helmet = self._named(wearer, Helmet, "iron helmet")
        worn, _ = wearer.wear("IRON HELMET")
        self.assertTrue(worn)
        self.assertIs(wearer.worn_items["HEAD"], helmet)

    def test_we_16_a_substring_of_the_key_matches(self):
        """WE-16"""
        from tests.game_typeclasses import Helmet

        wearer = self._wearer()
        helmet = self._named(wearer, Helmet, "slaying helm of mega doom")
        worn, _ = wearer.wear("doom")
        self.assertTrue(worn)
        self.assertIs(wearer.worn_items["HEAD"], helmet)

    def test_we_17_a_string_matching_nothing_is_refused_as_not_carried(self):
        """WE-17"""
        from tests.game_typeclasses import Helmet

        wearer = self._wearer()
        self._named(wearer, Helmet, "iron helmet")
        worn, message = wearer.wear("boots")
        self.assertFalse(worn)
        self.assertIn("boots", message)

    def test_we_18_a_string_matching_only_a_worn_item_says_already_worn(self):
        """WE-18"""
        from tests.game_typeclasses import Helmet

        wearer = self._wearer()
        self._named(wearer, Helmet, "iron helmet")
        wearer.wear("iron helmet")
        worn, message = wearer.wear("iron helmet")
        self.assertFalse(worn)
        # The refusal has to say which of the two things went wrong. "Not
        # carrying it" is both false and useless to someone wearing it.
        self.assertIn("already", message.lower())

    def test_we_19_of_several_matches_sharing_a_key_the_first_is_worn(self):
        """WE-19"""
        from tests.game_typeclasses import Ring

        wearer = self._wearer()
        first = self._named(wearer, Ring, "iron ring")
        self._named(wearer, Ring, "iron ring")
        worn, _ = wearer.wear("ring")
        self.assertTrue(worn)
        self.assertIs(wearer.worn_items["LEFT_HAND"], first)

    def test_we_20_matches_with_differing_keys_are_refused_with_the_typed_word(self):
        """WE-20"""
        from tests.game_typeclasses import Helmet, Ring

        wearer = self._wearer()
        self._named(wearer, Helmet, "iron helmet")
        self._named(wearer, Ring, "iron ring")
        worn, message = wearer.wear("iron")
        self.assertFalse(worn)
        # A question, not a refusal. Asserting only that it failed and named
        # the word would pass on "you are not carrying iron", which is the
        # wrong answer arrived at by not looking.
        self.assertIn("which", message.lower())
        self.assertIn("iron", message)
        self.assertEqual(wearer.get_all_worn(), [])

    def test_we_21_a_carried_item_wins_over_a_worn_one(self):
        """WE-21"""
        from tests.game_typeclasses import Ring

        wearer = self._wearer()
        first = self._named(wearer, Ring, "iron ring")
        second = self._named(wearer, Ring, "iron ring")
        wearer.wear(first)
        worn, _ = wearer.wear("ring")
        self.assertTrue(worn)
        self.assertIs(wearer.worn_items["RIGHT_HAND"], second)

    def test_we_22_an_object_is_worn_without_being_resolved(self):
        """WE-22"""
        from tests.game_typeclasses import Ring

        wearer = self._wearer()
        self._named(wearer, Ring, "iron ring")
        second = self._named(wearer, Ring, "iron ring")
        # Two items one string could not tell apart. Resolving would take the
        # first; an object path takes the one it was handed.
        worn, _ = wearer.wear(second)
        self.assertTrue(worn)
        self.assertIs(wearer.worn_items["LEFT_HAND"], second)

    # --- naming a slot -----------------------------------------------------

    def test_we_23_a_named_slot_is_chosen_over_an_earlier_free_group(self):
        """WE-23"""
        from tests.game_typeclasses import Ring

        wearer = self._wearer()
        ring = self._held(wearer, Ring)
        # Both hands free, and LEFT_HAND is declared first. Naming the right
        # one has to beat the item author's preference or the argument does
        # nothing an implementation that merely checks the slot wouldn't.
        worn, _ = wearer.wear(ring, slot="RIGHT_HAND")
        self.assertTrue(worn)
        self.assertIs(wearer.worn_items["RIGHT_HAND"], ring)
        self.assertIsNone(wearer.worn_items["LEFT_HAND"])

    def test_we_24_naming_one_slot_of_a_group_fills_the_whole_group(self):
        """WE-24"""
        from tests.game_typeclasses import Greatsword

        wearer = self._wearer()
        sword = self._held(wearer, Greatsword)
        worn, _ = wearer.wear(sword, slot="RIGHT_HAND")
        self.assertTrue(worn)
        self.assertIs(wearer.worn_items["RIGHT_HAND"], sword)
        self.assertIs(wearer.worn_items["LEFT_HAND"], sword)

    def test_we_25_a_named_slot_the_item_does_not_declare_is_refused(self):
        """WE-25"""
        from tests.game_typeclasses import Helmet

        wearer = self._wearer()
        helmet = self._held(wearer, Helmet)
        worn, message = wearer.wear(helmet, slot="LEFT_HAND")
        self.assertFalse(worn)
        self.assertIn("LEFT_HAND", message)
        self.assertIsNone(wearer.worn_items["LEFT_HAND"])
        self.assertIsNone(wearer.worn_items["HEAD"])

    def test_we_26_a_named_slot_this_wearer_does_not_have_is_refused(self):
        """WE-26"""
        from tests.game_typeclasses import Collar

        wearer = self._wearer()
        collar = self._held(wearer, Collar)
        worn, message = wearer.wear(collar, slot="DOG_NECK")
        self.assertFalse(worn)
        # The item declares DOG_NECK; this wearer has no such place. A player
        # naming a slot their body does not have needs to hear that, not that
        # the collar cannot go there.
        self.assertIn("DOG_NECK", message)
        self.assertIn("have no", message.lower())

    def test_we_27_a_named_slot_already_occupied_is_refused(self):
        """WE-27"""
        from tests.game_typeclasses import Ring

        wearer = self._wearer()
        first, second = self._held(wearer, Ring), self._held(wearer, Ring)
        wearer.wear(first)
        worn, message = wearer.wear(second, slot="LEFT_HAND")
        self.assertFalse(worn)
        self.assertTrue(message)
        # The free right hand is not a substitute — a named slot is a demand,
        # not a preference.
        self.assertIs(wearer.worn_items["LEFT_HAND"], first)
        self.assertIsNone(wearer.worn_items["RIGHT_HAND"])

    def test_we_28_a_slot_named_as_an_enum_member_works(self):
        """WE-28"""
        from tests.game_typeclasses import Ring
        from tests.slot_enums import WearSlot

        wearer = self._wearer()
        ring = self._held(wearer, Ring)
        worn, _ = wearer.wear(ring, slot=WearSlot.RIGHT_HAND)
        self.assertTrue(worn)
        self.assertIs(wearer.worn_items["RIGHT_HAND"], ring)

    def test_we_29_a_slot_can_be_named_while_the_item_is_a_string(self):
        """WE-29"""
        from tests.game_typeclasses import Ring

        wearer = self._wearer()
        ring = self._named(wearer, Ring, "iron ring")
        worn, _ = wearer.wear("iron ring", slot="RIGHT_HAND")
        self.assertTrue(worn)
        self.assertIs(wearer.worn_items["RIGHT_HAND"], ring)

    # --- the hooks ---------------------------------------------------------

    def test_we_30_at_pre_wear_allows_by_default(self):
        """WE-30"""
        from tests.game_typeclasses import Helmet

        wearer = self._wearer()
        helmet = self._held(wearer, Helmet)
        self.assertEqual(wearer.at_pre_wear(helmet), (True, ""))

    def test_we_31_a_consumer_refusing_stops_the_wearing(self):
        """WE-31"""
        from tests.game_typeclasses import Helmet, UnwearableHumanoid

        wearer = self._wearer(UnwearableHumanoid)
        helmet = self._held(wearer, Helmet)
        worn, _ = wearer.wear(helmet)
        self.assertFalse(worn)
        self.assertIsNone(wearer.worn_items["HEAD"])

    def test_we_32_the_consumers_reason_is_returned(self):
        """WE-32"""
        from tests.game_typeclasses import Helmet, UnwearableHumanoid

        wearer = self._wearer(UnwearableHumanoid)
        helmet = self._held(wearer, Helmet)
        _, message = wearer.wear(helmet)
        self.assertEqual(message, f"{helmet} will not go on.")

    def test_we_33_at_post_wear_sees_the_slots_already_filled(self):
        """WE-33"""
        from tests.game_typeclasses import Helmet, WatchfulHumanoid

        wearer = self._wearer(WatchfulHumanoid)
        helmet = self._held(wearer, Helmet)
        wearer.wear(helmet)
        _, _, worn_at_the_time = wearer.ndb.wear_calls[0]
        # A consumer recalculating from get_all_worn() has to see the item it
        # was just told about, or the hook has to be told the answer twice.
        self.assertEqual(worn_at_the_time, (helmet,))

    def test_we_34_at_post_wear_receives_the_slots_filled(self):
        """WE-34"""
        from tests.game_typeclasses import Greatsword, WatchfulHumanoid

        wearer = self._wearer(WatchfulHumanoid)
        sword = self._held(wearer, Greatsword)
        wearer.wear(sword)
        item, slots, _ = wearer.ndb.wear_calls[0]
        self.assertIs(item, sword)
        self.assertEqual(set(slots), {"LEFT_HAND", "RIGHT_HAND"})

    def test_we_35_at_post_wear_does_not_fire_when_refused(self):
        """WE-35"""
        from tests.game_typeclasses import Helmet, UnwearableWatcher

        wearer = self._wearer(UnwearableWatcher)
        helmet = self._held(wearer, Helmet)
        wearer.wear(helmet)
        self.assertIsNone(wearer.ndb.wear_calls)

    def test_we_36_restore_worn_fires_at_post_wear(self):
        """WE-36"""
        from evennia import create_object
        from tests.game_typeclasses import IdentifiedHelmet, WatchfulHumanoid

        wearer = self._wearer(WatchfulHumanoid)
        helmet = create_object(
            IdentifiedHelmet, key="helmet", location=wearer, nohome=True
        )
        wearer.wear(helmet)
        wearer.update_worn_equipment_record()
        # The rebuild: the record survives, the slots do not.
        wearer.worn_items = {name: None for name in wearer.worn_items}
        wearer.ndb.wear_calls = None

        wearer.restore_worn()
        # A ring of strength put back on without the hook leaves a character
        # wearing it and no stronger for it.
        self.assertEqual(len(wearer.ndb.wear_calls), 1)
        self.assertIs(wearer.ndb.wear_calls[0][0], helmet)


class RemoveTests(DjangoTestCase):
    """RM — freeing the slots an item occupies."""

    def _wearer(self):
        """Create one wearer. Not a test."""
        from evennia import create_object
        from tests.game_typeclasses import Humanoid

        return create_object(Humanoid, key="wearer", nohome=True)

    def _worn(self, wearer, typeclass):
        """Create an item in the wearer's contents and put it on."""
        from evennia import create_object

        item = create_object(
            typeclass, key=typeclass.__name__, location=wearer, nohome=True
        )
        wearer.wear(item)
        return item

    def test_rm_01_removing_frees_the_slot(self):
        """RM-01"""
        from tests.game_typeclasses import Helmet

        wearer = self._wearer()
        helmet = self._worn(wearer, Helmet)
        came_off, _ = wearer.remove(helmet)
        self.assertTrue(came_off)
        self.assertIsNone(wearer.worn_items["HEAD"])

    def test_rm_02_removing_frees_every_slot_it_occupied(self):
        """RM-02"""
        from tests.game_typeclasses import Greatsword

        wearer = self._wearer()
        sword = self._worn(wearer, Greatsword)
        wearer.remove(sword)
        self.assertIsNone(wearer.worn_items["LEFT_HAND"])
        self.assertIsNone(wearer.worn_items["RIGHT_HAND"])

    def test_rm_03_removing_something_not_worn_is_refused(self):
        """RM-03"""
        from evennia import create_object
        from tests.game_typeclasses import Helmet

        wearer = self._wearer()
        carried = create_object(Helmet, key="helmet", location=wearer, nohome=True)
        came_off, _ = wearer.remove(carried)
        self.assertFalse(came_off)

    def test_rm_04_removing_leaves_the_item_in_contents(self):
        """RM-04"""
        from tests.game_typeclasses import Helmet

        wearer = self._wearer()
        helmet = self._worn(wearer, Helmet)
        wearer.remove(helmet)
        self.assertIn(helmet, wearer.contents)

    def test_rm_05_removing_does_not_change_the_carried_weight(self):
        """RM-05"""
        from tests.game_typeclasses import Helmet

        wearer = self._wearer()
        helmet = self._worn(wearer, Helmet)
        helmet.weight = 2.0
        before = wearer.items_weight
        wearer.remove(helmet)
        self.assertEqual(wearer.items_weight, before)

    def test_rm_06_other_worn_items_are_unaffected(self):
        """RM-06"""
        from tests.game_typeclasses import Helmet, Ring

        wearer = self._wearer()
        helmet = self._worn(wearer, Helmet)
        ring = self._worn(wearer, Ring)
        wearer.remove(helmet)
        self.assertIs(wearer.worn_items["LEFT_HAND"], ring)

    def test_rm_07_a_removed_item_can_be_worn_again(self):
        """RM-07"""
        from tests.game_typeclasses import Helmet

        wearer = self._wearer()
        helmet = self._worn(wearer, Helmet)
        wearer.remove(helmet)
        worn, _ = wearer.wear(helmet)
        self.assertTrue(worn)
        self.assertIs(wearer.worn_items["HEAD"], helmet)

    def test_rm_10_the_hook_allows_removal_by_default(self):
        """RM-10"""
        from tests.game_typeclasses import Helmet

        wearer = self._wearer()
        allowed, _ = wearer.at_pre_remove(self._worn(wearer, Helmet))
        self.assertTrue(allowed)

    def test_rm_11_a_consumer_refusing_stops_the_removal(self):
        """RM-11"""
        from evennia import create_object
        from tests.game_typeclasses import CursedHumanoid, Helmet

        wearer = create_object(CursedHumanoid, key="cursed", nohome=True)
        helmet = create_object(Helmet, key="helmet", location=wearer, nohome=True)
        wearer.wear(helmet)
        came_off, _ = wearer.remove(helmet)
        self.assertFalse(came_off)
        self.assertTrue(wearer.is_worn(helmet))

    def test_rm_12_the_consumers_reason_is_returned(self):
        """RM-12"""
        from evennia import create_object
        from tests.game_typeclasses import CursedHumanoid, Helmet

        wearer = create_object(CursedHumanoid, key="cursed", nohome=True)
        helmet = create_object(Helmet, key="helmet", location=wearer, nohome=True)
        wearer.wear(helmet)
        _, said = wearer.remove(helmet)
        self.assertIn("will not come off", said)

    def test_rm_13_the_slots_are_untouched_when_removal_is_refused(self):
        """RM-13"""
        from evennia import create_object
        from tests.game_typeclasses import CursedHumanoid, Greatsword

        wearer = create_object(CursedHumanoid, key="cursed", nohome=True)
        sword = create_object(Greatsword, key="sword", location=wearer, nohome=True)
        wearer.wear(sword)
        wearer.remove(sword)
        self.assertIs(wearer.worn_items["LEFT_HAND"], sword)
        self.assertIs(wearer.worn_items["RIGHT_HAND"], sword)

    def test_rm_09_removing_one_of_two_identical_items_frees_only_that_one(self):
        """RM-09"""
        from tests.game_typeclasses import TwinRing

        wearer = self._wearer()
        first = self._worn(wearer, TwinRing)
        second = self._worn(wearer, TwinRing)
        wearer.remove(first)
        self.assertIsNone(wearer.worn_items["LEFT_HAND"])
        self.assertIs(wearer.worn_items["RIGHT_HAND"], second)

    def test_rm_08_both_outcomes_return_a_message(self):
        """RM-08"""
        from tests.game_typeclasses import Helmet

        wearer = self._wearer()
        helmet = self._worn(wearer, Helmet)
        _, said = wearer.remove(helmet)
        self.assertTrue(said)
        _, refused = wearer.remove(helmet)
        self.assertTrue(refused)

    # --- resolving a string ------------------------------------------------

    def _named(self, wearer, typeclass, key, wear=True):
        """Create a wearable under a key of the test's choosing.

        The `_worn` helper keys everything after its typeclass, which is fine
        while items are told apart by type. These cases tell them apart by
        name, so the name is the thing under test.
        """
        from evennia import create_object

        item = create_object(typeclass, key=key, location=wearer, nohome=True)
        if wear:
            wearer.wear(item)
        return item

    def test_rm_14_a_string_naming_a_worn_item_removes_it(self):
        """RM-14"""
        from tests.game_typeclasses import Helmet

        wearer = self._wearer()
        self._named(wearer, Helmet, "iron helmet")
        removed, _ = wearer.remove("iron helmet")
        self.assertTrue(removed)
        self.assertIsNone(wearer.worn_items["HEAD"])

    def test_rm_15_matching_ignores_case(self):
        """RM-15"""
        from tests.game_typeclasses import Helmet

        wearer = self._wearer()
        self._named(wearer, Helmet, "iron helmet")
        removed, _ = wearer.remove("IRON HELMET")
        self.assertTrue(removed)
        self.assertIsNone(wearer.worn_items["HEAD"])

    def test_rm_16_a_substring_of_the_key_matches(self):
        """RM-16"""
        from tests.game_typeclasses import Helmet

        wearer = self._wearer()
        self._named(wearer, Helmet, "slaying helm of mega doom")
        removed, _ = wearer.remove("doom")
        self.assertTrue(removed)
        self.assertIsNone(wearer.worn_items["HEAD"])

    def test_rm_17_a_string_matching_nothing_is_refused(self):
        """RM-17"""
        from tests.game_typeclasses import Helmet

        wearer = self._wearer()
        self._named(wearer, Helmet, "iron helmet")
        removed, message = wearer.remove("boots")
        self.assertFalse(removed)
        self.assertIn("boots", message)
        # "Not carrying" and "not wearing" are different answers, and this is
        # the one that has nothing at all. RM-18 is the other.
        self.assertIn("not carrying", message.lower())

    def test_rm_18_a_string_matching_only_a_carried_item_says_not_worn(self):
        """RM-18"""
        from tests.game_typeclasses import Helmet

        wearer = self._wearer()
        self._named(wearer, Helmet, "iron helmet", wear=False)
        removed, message = wearer.remove("iron")
        self.assertFalse(removed)
        # Searching only the worn items would say they are not carrying it,
        # when the useful answer is that they have it and are not wearing it.
        self.assertIn("not wearing", message.lower())
        # Names the item it found, not the word that was typed — which is the
        # only proof the second pass ran.
        self.assertIn("helmet", message.lower())

    def test_rm_19_of_several_matches_sharing_a_key_the_first_is_removed(self):
        """RM-19"""
        from tests.game_typeclasses import Ring

        wearer = self._wearer()
        first = self._named(wearer, Ring, "iron ring")
        second = self._named(wearer, Ring, "iron ring")
        removed, _ = wearer.remove("ring")
        self.assertTrue(removed)
        self.assertIsNone(wearer.worn_items["LEFT_HAND"])
        self.assertIs(wearer.worn_items["RIGHT_HAND"], second)
        self.assertFalse(wearer.is_worn(first))

    def test_rm_20_matches_with_differing_keys_are_refused_with_the_typed_word(self):
        """RM-20"""
        from tests.game_typeclasses import Helmet, Ring

        wearer = self._wearer()
        self._named(wearer, Helmet, "iron helmet")
        self._named(wearer, Ring, "iron ring")
        removed, message = wearer.remove("iron")
        self.assertFalse(removed)
        # A question, not a refusal. Asserting only that it failed and named
        # the word would pass on "you are not wearing iron", which is the
        # wrong answer arrived at by not looking.
        self.assertIn("which", message.lower())
        self.assertIn("iron", message)
        self.assertEqual(len(wearer.get_all_worn()), 2)

    def test_rm_21_a_worn_item_wins_over_a_carried_one(self):
        """RM-21"""
        from tests.game_typeclasses import Ring

        wearer = self._wearer()
        worn = self._named(wearer, Ring, "iron ring")
        carried = self._named(wearer, Ring, "iron ring", wear=False)
        removed, _ = wearer.remove("ring")
        self.assertTrue(removed)
        self.assertFalse(wearer.is_worn(worn))
        self.assertIn(carried, wearer.get_carried())

    def test_rm_22_an_object_is_removed_without_being_resolved(self):
        """RM-22"""
        from tests.game_typeclasses import Ring

        wearer = self._wearer()
        self._named(wearer, Ring, "iron ring")
        second = self._named(wearer, Ring, "iron ring")
        # Two items one string could not tell apart. Resolving would take the
        # first; an object path takes the one it was handed.
        removed, _ = wearer.remove(second)
        self.assertTrue(removed)
        self.assertIsNone(wearer.worn_items["RIGHT_HAND"])

    # --- naming a slot -----------------------------------------------------

    def test_rm_23_a_named_slot_alone_removes_what_is_in_it(self):
        """RM-23"""
        from tests.game_typeclasses import Helmet

        wearer = self._wearer()
        helmet = self._worn(wearer, Helmet)
        removed, _ = wearer.remove(slot="HEAD")
        self.assertTrue(removed)
        self.assertIsNone(wearer.worn_items["HEAD"])
        self.assertIn(helmet, wearer.get_carried())

    def test_rm_24_naming_one_slot_frees_every_slot_it_occupied(self):
        """RM-24"""
        from tests.game_typeclasses import Greatsword

        wearer = self._wearer()
        self._worn(wearer, Greatsword)
        removed, _ = wearer.remove(slot="RIGHT_HAND")
        self.assertTrue(removed)
        self.assertIsNone(wearer.worn_items["RIGHT_HAND"])
        self.assertIsNone(wearer.worn_items["LEFT_HAND"])

    def test_rm_25_a_named_slot_this_wearer_does_not_have_is_refused(self):
        """RM-25"""
        wearer = self._wearer()
        removed, message = wearer.remove(slot="DOG_NECK")
        self.assertFalse(removed)
        self.assertIn("DOG_NECK", message)
        self.assertIn("have no", message.lower())

    def test_rm_26_a_named_slot_holding_nothing_is_refused(self):
        """RM-26"""
        wearer = self._wearer()
        removed, message = wearer.remove(slot="HEAD")
        self.assertFalse(removed)
        # Different from having no such slot: this one exists and is empty,
        # and only that answer invites the player to look again.
        self.assertIn("nothing", message.lower())
        self.assertIn("HEAD", message)

    def test_rm_27_an_item_and_a_slot_remove_that_item_from_that_slot(self):
        """RM-27"""
        from tests.game_typeclasses import Ring

        wearer = self._wearer()
        ring = self._named(wearer, Ring, "iron ring")
        removed, _ = wearer.remove("iron ring", slot="LEFT_HAND")
        self.assertTrue(removed)
        self.assertFalse(wearer.is_worn(ring))

    def test_rm_28_an_item_worn_elsewhere_than_the_named_slot_is_refused(self):
        """RM-28"""
        from tests.game_typeclasses import Ring

        wearer = self._wearer()
        ring = self._named(wearer, Ring, "iron ring")
        # Worn on the left; the right was named.
        removed, message = wearer.remove("iron ring", slot="RIGHT_HAND")
        self.assertFalse(removed)
        self.assertTrue(message)
        self.assertIs(wearer.worn_items["LEFT_HAND"], ring)

    def test_rm_29_of_two_items_sharing_a_key_the_one_in_the_slot_is_removed(self):
        """RM-29"""
        from tests.game_typeclasses import Ring

        wearer = self._wearer()
        left = self._named(wearer, Ring, "iron ring")
        right = self._named(wearer, Ring, "iron ring")
        # Same key, one on each hand. "Which ring do you mean?" has no answer
        # a player could give, so the slot is the only way to say.
        removed, _ = wearer.remove("iron ring", slot="RIGHT_HAND")
        self.assertTrue(removed)
        self.assertFalse(wearer.is_worn(right))
        self.assertIs(wearer.worn_items["LEFT_HAND"], left)

    def test_rm_30_a_slot_named_as_an_enum_member_works(self):
        """RM-30"""
        from tests.game_typeclasses import Helmet
        from tests.slot_enums import WearSlot

        wearer = self._wearer()
        self._worn(wearer, Helmet)
        removed, _ = wearer.remove(slot=WearSlot.HEAD)
        self.assertTrue(removed)
        self.assertIsNone(wearer.worn_items["HEAD"])

    def test_rm_31_neither_an_item_nor_a_slot_is_refused(self):
        """RM-31"""
        from tests.game_typeclasses import Helmet

        wearer = self._wearer()
        helmet = self._worn(wearer, Helmet)
        removed, message = wearer.remove()
        self.assertFalse(removed)
        self.assertTrue(message)
        # A command that failed to parse must not strip anything by default.
        self.assertIs(wearer.worn_items["HEAD"], helmet)

    # --- the post hook -----------------------------------------------------

    def test_rm_32_at_post_remove_sees_the_slots_already_freed(self):
        """RM-32"""
        from evennia import create_object
        from tests.game_typeclasses import Helmet, WatchfulHumanoid

        wearer = create_object(WatchfulHumanoid, key="wearer", nohome=True)
        helmet = create_object(Helmet, key="Helmet", location=wearer, nohome=True)
        wearer.wear(helmet)
        wearer.remove(helmet)
        _, _, worn_at_the_time = wearer.ndb.remove_calls[0]
        self.assertEqual(worn_at_the_time, ())

    def test_rm_33_at_post_remove_receives_the_slots_freed(self):
        """RM-33"""
        from evennia import create_object
        from tests.game_typeclasses import Greatsword, WatchfulHumanoid

        wearer = create_object(WatchfulHumanoid, key="wearer", nohome=True)
        sword = create_object(Greatsword, key="sword", location=wearer, nohome=True)
        wearer.wear(sword)
        wearer.remove(sword)
        item, slots, _ = wearer.ndb.remove_calls[0]
        self.assertIs(item, sword)
        # The only moment this is knowable — the slots are freed by now, so
        # where it sat exists nowhere else.
        self.assertEqual(set(slots), {"LEFT_HAND", "RIGHT_HAND"})

    def test_rm_34_at_post_remove_does_not_fire_when_refused(self):
        """RM-34"""
        from evennia import create_object
        from tests.game_typeclasses import Helmet, StuckWatcher

        wearer = create_object(StuckWatcher, key="wearer", nohome=True)
        helmet = create_object(Helmet, key="Helmet", location=wearer, nohome=True)
        wearer.wear(helmet)
        wearer.remove(helmet)
        # Firing anyway would strip a ring's bonus from someone still wearing
        # it.
        self.assertIsNone(wearer.ndb.remove_calls)


class IdentityTests(DjangoTestCase):
    """ID, ER — what an item is known by, and writing down what is worn."""

    def _wearer(self):
        """Create one wearer. Not a test."""
        from evennia import create_object
        from tests.game_typeclasses import Humanoid

        return create_object(Humanoid, key="wearer", nohome=True)

    def _held(self, wearer, typeclass):
        """Create an item in the wearer's contents, unworn."""
        from evennia import create_object

        return create_object(
            typeclass, key=typeclass.__name__, location=wearer, nohome=True
        )

    def _worn(self, wearer, typeclass):
        """Create an item in the wearer's contents and put it on."""
        item = self._held(wearer, typeclass)
        wearer.wear(item)
        return item

    # --- ID ---------------------------------------------------------------

    def test_id_01_the_identity_is_read_from_the_named_attribute(self):
        """ID-01"""
        from tests.game_typeclasses import IdentifiedHelmet

        wearer = self._wearer()
        self.assertEqual(self._held(wearer, IdentifiedHelmet).wearslot_identity, "nft:1")

    def test_id_02_an_item_without_the_attribute_has_no_identity(self):
        """ID-02"""
        from tests.game_typeclasses import Helmet

        wearer = self._wearer()
        self.assertIsNone(self._held(wearer, Helmet).wearslot_identity)

    def test_id_03_a_consumer_overriding_the_accessor_wins(self):
        """ID-03"""
        from tests.game_typeclasses import SelfIdentifyingHelmet

        wearer = self._wearer()
        self.assertEqual(
            self._held(wearer, SelfIdentifyingHelmet).wearslot_identity,
            "minted-elsewhere",
        )

    # --- ER ---------------------------------------------------------------

    def test_er_01_nothing_worn_gives_an_empty_record(self):
        """ER-01"""
        wearer = self._wearer()
        wearer.update_worn_equipment_record()
        self.assertEqual(wearer.worn_equipment_record, set())

    def test_er_02_a_worn_items_identity_is_recorded(self):
        """ER-02"""
        from tests.game_typeclasses import IdentifiedHelmet

        wearer = self._wearer()
        self._worn(wearer, IdentifiedHelmet)
        wearer.update_worn_equipment_record()
        self.assertEqual(wearer.worn_equipment_record, {"nft:1"})

    def test_er_03_a_carried_item_is_not_recorded(self):
        """ER-03"""
        from tests.game_typeclasses import IdentifiedHelmet

        wearer = self._wearer()
        self._held(wearer, IdentifiedHelmet)
        wearer.update_worn_equipment_record()
        self.assertEqual(wearer.worn_equipment_record, set())

    def test_er_04_an_item_with_no_identity_is_skipped(self):
        """ER-04"""
        from tests.game_typeclasses import Helmet

        wearer = self._wearer()
        self._worn(wearer, Helmet)
        wearer.update_worn_equipment_record()
        self.assertEqual(wearer.worn_equipment_record, set())

    def test_er_05_an_item_taken_off_is_no_longer_in_the_record(self):
        """ER-05"""
        from tests.game_typeclasses import IdentifiedHelmet

        wearer = self._wearer()
        helmet = self._worn(wearer, IdentifiedHelmet)
        wearer.update_worn_equipment_record()
        wearer.remove(helmet)
        wearer.update_worn_equipment_record()
        self.assertEqual(wearer.worn_equipment_record, set())

    def test_er_06_calling_it_twice_gives_the_same_result(self):
        """ER-06"""
        from tests.game_typeclasses import IdentifiedHelmet

        wearer = self._wearer()
        self._worn(wearer, IdentifiedHelmet)
        wearer.update_worn_equipment_record()
        wearer.update_worn_equipment_record()
        self.assertEqual(wearer.worn_equipment_record, {"nft:1"})

    def test_er_07_the_record_is_persisted_not_held_in_memory(self):
        """ER-07"""
        from tests.game_typeclasses import IdentifiedHelmet

        wearer = self._wearer()
        self._worn(wearer, IdentifiedHelmet)
        wearer.update_worn_equipment_record()
        # Straight out of the attribute handler, not the property that wrote
        # it — an ndb value would not be there at all.
        self.assertEqual(set(wearer.attributes.get("worn_equipment_record")), {"nft:1"})


class RestoreWornTests(DjangoTestCase):
    """RW — putting the recorded equipment back on after a rebuild."""

    def _dressed(self):
        """A wearer with an identified helmet on, and a record of it.

        Stands in for the state just before an archive: the gear is worn and
        written down. Not a test.
        """
        from evennia import create_object
        from tests.game_typeclasses import Humanoid, IdentifiedHelmet

        wearer = create_object(Humanoid, key="wearer", nohome=True)
        helmet = create_object(
            IdentifiedHelmet, key="helmet", location=wearer, nohome=True
        )
        wearer.wear(helmet)
        wearer.update_worn_equipment_record()
        return wearer, helmet

    def _rebuilt(self):
        """The same wearer after a rebuild: record intact, nothing worn.

        The slots are emptied rather than the objects remade — what matters to
        `restore_worn()` is a record with no matching assignments, which is
        exactly what a restored character has.
        """
        wearer, helmet = self._dressed()
        wearer.remove(helmet)
        return wearer, helmet

    def test_rw_01_an_item_in_the_record_is_worn(self):
        """RW-01"""
        wearer, helmet = self._rebuilt()
        wearer.restore_worn()
        self.assertTrue(wearer.is_worn(helmet))

    def test_rw_02_an_item_not_in_the_record_stays_carried(self):
        """RW-02"""
        from evennia import create_object
        from tests.game_typeclasses import OtherIdentifiedHelmet

        wearer, _ = self._rebuilt()
        stranger = create_object(
            OtherIdentifiedHelmet, key="other", location=wearer, nohome=True
        )
        wearer.restore_worn()
        self.assertFalse(wearer.is_worn(stranger))
        self.assertIn(stranger, wearer.get_carried())

    def test_rw_03_an_item_already_worn_returns_wears_refusal(self):
        """RW-03"""
        wearer, _ = self._dressed()
        outcomes = wearer.restore_worn()
        self.assertTrue(outcomes)
        self.assertFalse(any(worn for worn, _ in outcomes))
        self.assertIn("already wearing", outcomes[0][1])

    def test_rw_04_an_item_that_cannot_be_worn_returns_wears_refusal(self):
        """RW-04"""
        from tests.game_typeclasses import Humanoid
        from tests.slot_enums import WearSlot

        wearer, helmet = self._rebuilt()
        # The slot the helmet needs is gone from the body plan since the
        # record was written.
        with mock.patch.object(Humanoid, "body_slots", (WearSlot.BODY,)):
            wearer.at_init()
            outcomes = wearer.restore_worn()
        self.assertFalse(any(worn for worn, _ in outcomes))
        self.assertIn(helmet, wearer.get_carried())

    def test_rw_06_an_item_that_is_not_wearable_is_passed_over(self):
        """RW-06"""
        from evennia import create_object
        from tests.game_typeclasses import CarriableThing

        wearer, helmet = self._rebuilt()
        create_object(CarriableThing, key="rock", location=wearer, nohome=True)
        wearer.restore_worn()
        self.assertTrue(wearer.is_worn(helmet))

    def test_rw_05_the_record_is_unchanged_by_restoring(self):
        """RW-05"""
        wearer, _ = self._rebuilt()
        before = set(wearer.worn_equipment_record)
        wearer.restore_worn()
        self.assertEqual(set(wearer.worn_equipment_record), before)


class WornAndCarriedTests(DjangoTestCase):
    """GW, GC — what a wearer has on, and what it merely holds."""

    def _wearer(self):
        """Create one wearer. Not a test."""
        from evennia import create_object
        from tests.game_typeclasses import Humanoid

        return create_object(Humanoid, key="wearer", nohome=True)

    def _held(self, wearer, typeclass):
        """Create an item in the wearer's contents, unworn."""
        from evennia import create_object

        return create_object(
            typeclass, key=typeclass.__name__, location=wearer, nohome=True
        )

    def _worn(self, wearer, typeclass):
        """Create an item in the wearer's contents and put it on."""
        item = self._held(wearer, typeclass)
        wearer.wear(item)
        return item

    # --- GW ---------------------------------------------------------------

    def test_gw_01_nothing_worn_gives_an_empty_result(self):
        """GW-01"""
        self.assertEqual(self._wearer().get_all_worn(), [])

    def test_gw_02_a_worn_item_is_listed(self):
        """GW-02"""
        from tests.game_typeclasses import Helmet

        wearer = self._wearer()
        helmet = self._worn(wearer, Helmet)
        self.assertEqual(wearer.get_all_worn(), [helmet])

    def test_gw_03_a_multi_slot_item_is_listed_once(self):
        """GW-03"""
        from tests.game_typeclasses import Greatsword

        wearer = self._wearer()
        sword = self._worn(wearer, Greatsword)
        self.assertEqual(wearer.get_all_worn(), [sword])

    def test_gw_04_a_carried_item_is_not_listed(self):
        """GW-04"""
        from tests.game_typeclasses import Helmet

        wearer = self._wearer()
        self._held(wearer, Helmet)
        self.assertEqual(wearer.get_all_worn(), [])

    def test_gw_05_a_deleted_item_drops_out(self):
        """GW-05"""
        from tests.game_typeclasses import Helmet

        wearer = self._wearer()
        helmet = self._worn(wearer, Helmet)
        helmet.delete()
        self.assertEqual(wearer.get_all_worn(), [])

    def test_gw_06_of_two_equal_items_only_the_worn_one_is_listed(self):
        """GW-06"""
        from tests.game_typeclasses import TwinRing

        wearer = self._wearer()
        worn = self._worn(wearer, TwinRing)
        self._held(wearer, TwinRing)
        self.assertEqual(wearer.get_all_worn(), [worn])

    # --- GC ---------------------------------------------------------------

    def test_gc_01_empty_contents_gives_an_empty_result(self):
        """GC-01"""
        self.assertEqual(self._wearer().get_carried(), [])

    def test_gc_02_a_carried_item_is_listed(self):
        """GC-02"""
        from tests.game_typeclasses import Helmet

        wearer = self._wearer()
        helmet = self._held(wearer, Helmet)
        self.assertEqual(wearer.get_carried(), [helmet])

    def test_gc_03_a_worn_item_is_not_listed(self):
        """GC-03"""
        from tests.game_typeclasses import Helmet

        wearer = self._wearer()
        self._worn(wearer, Helmet)
        self.assertEqual(wearer.get_carried(), [])

    def test_gc_04_a_multi_slot_worn_item_is_not_listed(self):
        """GC-04"""
        from tests.game_typeclasses import Greatsword

        wearer = self._wearer()
        self._worn(wearer, Greatsword)
        self.assertEqual(wearer.get_carried(), [])

    def test_gc_06_of_two_equal_items_the_unworn_one_is_listed(self):
        """GC-06"""
        from tests.game_typeclasses import TwinRing

        wearer = self._wearer()
        self._worn(wearer, TwinRing)
        carried = self._held(wearer, TwinRing)
        self.assertEqual(wearer.get_carried(), [carried])

    def test_gc_05_worn_and_carried_account_for_all_contents(self):
        """GC-05"""
        from tests.game_typeclasses import Greatsword, Helmet, Ring

        wearer = self._wearer()
        self._worn(wearer, Greatsword)
        self._worn(wearer, Helmet)
        self._held(wearer, Ring)
        self.assertEqual(
            set(wearer.get_all_worn()) | set(wearer.get_carried()),
            set(wearer.contents),
        )


class TargetingFilterTests(DjangoTestCase):
    """TG — the filters this library publishes for evennia-targeting."""

    def _wearer(self):
        """Create one wearer. Not a test."""
        from evennia import create_object
        from tests.game_typeclasses import Humanoid

        return create_object(Humanoid, key="wearer", nohome=True)

    def _held(self, wearer, typeclass):
        """Create an item in the wearer's contents, unworn."""
        from evennia import create_object

        return create_object(
            typeclass, key=typeclass.__name__, location=wearer, nohome=True
        )

    def _worn(self, wearer, typeclass):
        """Create an item in the wearer's contents and put it on."""
        item = self._held(wearer, typeclass)
        wearer.wear(item)
        return item

    # --- f_worn_by --------------------------------------------------------

    def test_tg_01_f_worn_by_passes_the_factory_validator(self):
        """TG-01"""
        from tests.game_typeclasses import Helmet

        wearer = self._wearer()
        helmet = self._worn(wearer, Helmet)
        self.assertEqual(
            validate_factory(f_worn_by, (wearer,), fixtures=(helmet, wearer)), []
        )

    def test_tg_02_a_worn_item_passes(self):
        """TG-02"""
        from tests.game_typeclasses import Helmet

        wearer = self._wearer()
        helmet = self._worn(wearer, Helmet)
        self.assertTrue(f_worn_by(wearer)(helmet, wearer))

    def test_tg_03_a_carried_item_does_not(self):
        """TG-03"""
        from tests.game_typeclasses import Helmet, Ring

        wearer = self._wearer()
        self._worn(wearer, Helmet)
        ring = self._held(wearer, Ring)
        self.assertFalse(f_worn_by(wearer)(ring, wearer))

    def test_tg_04_a_multi_slot_item_passes(self):
        """TG-04"""
        from tests.game_typeclasses import Greatsword

        wearer = self._wearer()
        sword = self._worn(wearer, Greatsword)
        self.assertTrue(f_worn_by(wearer)(sword, wearer))

    def test_tg_05_of_two_equal_items_only_the_worn_one_passes(self):
        """TG-05"""
        from tests.game_typeclasses import TwinRing

        wearer = self._wearer()
        worn = self._worn(wearer, TwinRing)
        carried = self._held(wearer, TwinRing)
        is_worn = f_worn_by(wearer)
        self.assertTrue(is_worn(worn, wearer))
        self.assertFalse(is_worn(carried, wearer))

    def test_tg_06_a_wearer_with_nothing_on_matches_nothing(self):
        """TG-06"""
        from tests.game_typeclasses import Helmet

        wearer = self._wearer()
        helmet = self._held(wearer, Helmet)
        self.assertFalse(f_worn_by(wearer)(helmet, wearer))

    def test_tg_07_the_occupied_slots_are_read_once_at_build_time(self):
        """TG-07"""
        from tests.game_typeclasses import Helmet

        wearer = self._wearer()
        helmet = self._worn(wearer, Helmet)
        is_worn = f_worn_by(wearer)
        wearer.remove(helmet)
        self.assertTrue(is_worn(helmet, wearer))

    # --- f_identity_in ----------------------------------------------------

    def test_tg_08_f_identity_in_passes_the_factory_validator(self):
        """TG-08"""
        from tests.game_typeclasses import IdentifiedHelmet

        wearer = self._wearer()
        helmet = self._held(wearer, IdentifiedHelmet)
        self.assertEqual(
            validate_factory(f_identity_in, ({"nft:1"},), fixtures=(helmet, wearer)),
            [],
        )

    def test_tg_09_an_item_whose_identity_is_in_the_set_passes(self):
        """TG-09"""
        from tests.game_typeclasses import IdentifiedHelmet

        wearer = self._wearer()
        helmet = self._held(wearer, IdentifiedHelmet)
        self.assertTrue(f_identity_in({"nft:1"})(helmet, wearer))

    def test_tg_10_an_item_whose_identity_is_not_in_the_set_does_not(self):
        """TG-10"""
        from tests.game_typeclasses import IdentifiedHelmet

        wearer = self._wearer()
        helmet = self._held(wearer, IdentifiedHelmet)
        self.assertFalse(f_identity_in({"nft:2"})(helmet, wearer))

    def test_tg_11_an_item_with_no_identity_attribute_is_passed_over(self):
        """TG-11"""
        from tests.game_typeclasses import CarriableThing

        wearer = self._wearer()
        rock = self._held(wearer, CarriableThing)
        self.assertFalse(f_identity_in({"nft:1"})(rock, wearer))

    def test_tg_12_an_empty_set_matches_nothing_rather_than_raising(self):
        """TG-12"""
        from tests.game_typeclasses import IdentifiedHelmet

        wearer = self._wearer()
        helmet = self._held(wearer, IdentifiedHelmet)
        self.assertFalse(f_identity_in(set())(helmet, wearer))


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
