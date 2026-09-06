# SPDX-License-Identifier: BSD-3-Clause
"""Real Evennia typeclasses carrying the library's mixins, for tests that
create objects.

``AttributeProperty`` needs an object with an attribute handler behind it, so
the CR cases create one of these rather than faking one.

This module imports Evennia, so it is imported inside a test body rather than
at module scope.
"""

from evennia import DefaultObject

from evennia_equipment.carriable import (
    EquipmentCarriableMixin,
    NonNegativeNumberProperty,
    WeightProperty,
)
from evennia_equipment.carrying import EquipmentCarryingMixin


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
