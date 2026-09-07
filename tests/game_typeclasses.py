# SPDX-License-Identifier: BSD-3-Clause
"""Real Evennia typeclasses carrying the library's mixins, for tests that
create objects.

``AttributeProperty`` needs an object with an attribute handler behind it, so
the CR cases create one of these rather than faking one.

This module imports Evennia, so it is imported inside a test body rather than
at module scope.
"""

from evennia import DefaultObject
from evennia.typeclasses.attributes import AttributeProperty

from evennia_equipment.carriable import (
    EquipmentCarriableMixin,
    NonNegativeNumberProperty,
    WeightProperty,
)
from evennia_equipment.carrying import EquipmentCarryingMixin
from evennia_equipment.container import EquipmentContainerMixin
from evennia_equipment.wearable import EquipmentWearableMixin, WearslotProperty
from evennia_equipment.wearslots import EquipmentWearslotsMixin
from tests.slot_enums import WearSlot


class CarriableThing(EquipmentCarriableMixin, DefaultObject):
    """Anything that can be picked up. Declares nothing of its own, so it
    carries the library's default weight. CR-01."""


class HeavyThing(CarriableThing):
    """A subclass overriding the weight default, as a consumer's item types do
    — re-declaring the property, not assigning a plain class attribute, which
    would shadow the descriptor and lose both validation and persistence.
    CR-02."""

    weight = WeightProperty(3.0)


class PaddedThing(CarriableThing):
    """Contributes more than it weighs, standing in for how a container will
    behave once it exists. EW-02."""

    @property
    def effective_weight(self):
        return self.weight + 1.0


class NoisyThing(CarriableThing):
    """Records that its own hook ran, and still calls through. WC-04."""

    def at_weight_changed(self):
        self.ndb.weight_change_seen = (self.ndb.weight_change_seen or 0) + 1
        return super().at_weight_changed()


class Carrier(EquipmentCarryingMixin, DefaultObject):
    """Anything that holds things and totals their weight. Deliberately not a
    character — nothing here needs one. CA cases."""


class BulkyCarrier(Carrier):
    """Overrides the capacity default, as a consumer's typeclass does. CP-03."""

    max_carrying_capacity = NonNegativeNumberProperty(20.0)


class PurseCarrier(Carrier):
    """A carrier holding weight that is not an object, and capacity that comes
    from somewhere the library cannot see. Both read from ``ndb`` so a test can
    change them mid-flight. TW-03, TW-04, CP-07."""

    def extra_weight(self):
        return self.ndb.coin_weight or 0.0

    def extra_capacity(self):
        return self.ndb.strength_bonus or 0.0


class Container(EquipmentContainerMixin, DefaultObject):
    """A backpack — carried, and carrying. CN cases."""


class PanniersContainer(Container):
    """Contributes only its own weight, as a mount's panniers do. CN-13."""

    @property
    def effective_weight(self):
        return self.weight


class PurseContainer(Container):
    """A container holding weight that is not an object. CN-12."""

    def extra_weight(self):
        return self.ndb.coin_weight or 0.0


class WearableThing(EquipmentWearableMixin, DefaultObject):
    """Anything that can be worn. Declares nothing, so a test sets its slots.
    WR cases."""


class Helm(WearableThing):
    """Declares its slots on the class, as a consumer's item types do. WR-09."""

    wearslot = WearslotProperty([["HEAD"]])


class MistypedHelm(WearableThing):
    """A class-level default naming a slot the enum does not hold. WR-09."""

    wearslot = WearslotProperty([["HAED"]])


class Humanoid(EquipmentWearslotsMixin, DefaultObject):
    """A wearer with the humanoid body plan. WS cases."""

    body_slots = (
        WearSlot.HEAD,
        WearSlot.BODY,
        WearSlot.LEFT_HAND,
        WearSlot.RIGHT_HAND,
    )


class CursedHumanoid(Humanoid):
    """A wearer whose gear will not come off, standing in for a consumer's
    curse, paralysis or combat rule. RM-11, RM-12, RM-13."""

    def at_pre_remove(self, item):
        return (False, f"{item} will not come off.")


class Dog(EquipmentWearslotsMixin, DefaultObject):
    """A wearer with a different body plan, so body_slots is proved to be
    read rather than assumed. WS-04."""

    body_slots = (WearSlot.DOG_NECK, WearSlot.DOG_BODY)


class Helmet(WearableThing):
    """One group, one slot — the ordinary case. WE-01."""

    wearslot = WearslotProperty([["HEAD"]])


class Greatsword(WearableThing):
    """One group taking two slots at once. WE-02, WE-05."""

    wearslot = WearslotProperty([["LEFT_HAND", "RIGHT_HAND"]])


class Ring(WearableThing):
    """Two groups of one, so a second ring lands on the other hand. WE-03,
    WE-04."""

    wearslot = WearslotProperty([["LEFT_HAND"], ["RIGHT_HAND"]])


class TwinRing(WearableThing):
    """A ring that compares equal to any other of its kind, as a consumer's
    typeclass may if it compares by key or by token id. RM-09."""

    wearslot = WearslotProperty([["LEFT_HAND"], ["RIGHT_HAND"]])

    def __eq__(self, other):
        return isinstance(other, TwinRing)

    def __hash__(self):
        return hash(TwinRing)


class IdentifiedHelmet(Helmet):
    """A helmet carrying the attribute EQUIPMENT_IDENTITY_ATTRIBUTE names, as
    a game's own items do. ID-01, ER cases."""

    token_id = AttributeProperty("nft:1")


class OtherIdentifiedHelmet(Helmet):
    """A second identified helmet, so a record can hold more than one. ER-05."""

    token_id = AttributeProperty("nft:2")


class SelfIdentifyingHelmet(Helmet):
    """Keeps its identity somewhere the setting does not name, and overrides
    the accessor to say so. ID-03."""

    @property
    def wearslot_identity(self):
        return "minted-elsewhere"


class Collar(WearableThing):
    """Declares a slot no humanoid has. WE-06, WE-10."""

    wearslot = WearslotProperty([["DOG_NECK"]])


class Nowhere(DefaultObject):
    """Somewhere to move an object to, so leaving is a real move. Carries no
    mixin, so it is also the object PR-01 tries to pick up."""


class _RecordingHooks:
    """Records that it was reached, standing in for another library's mixin
    further down the chain. Sits *after* the library's mixin in the MRO, so it
    is only reached if the library calls ``super()``."""

    def at_pre_object_receive(self, arriving_object, source_location, **kwargs):
        self.ndb.pre_receive_super_ran = True
        return super().at_pre_object_receive(arriving_object, source_location, **kwargs)

    def at_object_receive(self, moved_obj, source_location, move_type="move", **kwargs):
        self.ndb.receive_super_ran = True
        return super().at_object_receive(
            moved_obj, source_location, move_type=move_type, **kwargs
        )

    def at_object_leave(self, moved_obj, target_location, move_type="move", **kwargs):
        self.ndb.leave_super_ran = True
        return super().at_object_leave(
            moved_obj, target_location, move_type=move_type, **kwargs
        )

    def at_init(self):
        self.ndb.init_super_ran = True
        return super().at_init()


class RecordingCarrier(EquipmentCarryingMixin, _RecordingHooks, DefaultObject):
    """A carrier with a witness below it in the MRO. RC-03, LV-02, IN-03."""


class _RefusingHooks:
    """Refuses every arrival, standing in for another library's veto."""

    def at_pre_object_receive(self, arriving_object, source_location, **kwargs):
        return False


class RefusingCarrier(EquipmentCarryingMixin, _RefusingHooks, DefaultObject):
    """A carrier whose chain refuses everything, so the library must not
    overrule it. PR-03."""
