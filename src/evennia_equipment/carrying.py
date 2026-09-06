# SPDX-License-Identifier: BSD-3-Clause
"""EquipmentCarryingMixin — an object that carries others and totals their weight.

The total is rebuilt from scratch on every weight-changing event rather than
adjusted up and down. Incremental tracking drifts: ``obj.delete()`` does not
fire ``at_object_leave()`` — in Evennia's ``objects.py`` that hook is called
only from ``move_to()`` — so a deleted object would leave its weight behind
permanently. Rebuilding means a missed event costs one stale reading, corrected
by the next rebuild.
"""

from evennia_equipment.carriable import (
    EquipmentCarriableMixin,
    NonNegativeNumberProperty,
)
from evennia_equipment.log import equipment_log


class EquipmentCarryingMixin:
    """Gives an object a running total of what its contents weigh.

    Mix into anything that holds things — a character, a mob, a mount.
    """

    # Rebuilt from scratch by _recalculate_item_weight(); never adjusted.
    items_weight = NonNegativeNumberProperty(0.0)

    # What equipment and the game have set. Unlimited by default: infinity is a
    # non-negative float, so it needs no special case in any query below, and
    # the library is not in a position to invent a game's balance number.
    max_carrying_capacity = NonNegativeNumberProperty(float("inf"))

    def extra_weight(self):
        """Weight this carrier holds that is not an object in ``contents``.

        Coin, ore, anything the game tracks as a balance. Computed when the
        total is read rather than stored, because nothing tells the library
        when a balance changes.

        Override to add it; the library carries none of its own.
        """
        return 0.0

    def extra_capacity(self):
        """Capacity derived from state the library cannot see.

        A strength score, a spell, a mount. Computed on read for the same
        reason as ``extra_weight()`` — so nothing has to be recalculated when
        the underlying state changes.

        Override to add it; the library carries none of its own.
        """
        return 0.0

    @property
    def current_weight_carried(self):
        """Everything this carrier is carrying, by weight."""
        return self.items_weight + self.extra_weight()

    @property
    def effective_capacity(self):
        """What this carrier can hold, all sources counted."""
        return self.max_carrying_capacity + self.extra_capacity()

    def get_remaining_capacity(self):
        """How much more can be taken on, never below zero."""
        return max(0.0, self.effective_capacity - self.current_weight_carried)

    def can_carry(self, additional):
        """Whether ``additional`` more weight would still fit.

        Returns:
            bool: True if it fits. What to do when it does not is the game's —
            refusing the move, allowing it with a penalty, and ignoring it are
            all reasonable, and none of them is the library's call.
        """
        return self.current_weight_carried + additional <= self.effective_capacity

    @property
    def is_encumbered(self):
        """Whether this carrier is over its capacity."""
        return self.current_weight_carried > self.effective_capacity

    def _recalculate_item_weight(self, exclude=None):
        """Rebuild ``items_weight`` from what is currently in ``contents``.

        Args:
            exclude (object, optional): An object to leave out of the sum.
                ``at_object_leave`` fires before the object has actually left
                ``contents``, so the departing object is named here.

        Returns:
            None: The result is stored in ``items_weight``.
        """
        # effective_weight, not weight: a container answers for itself, so
        # there is no container branch here and never needs to be one.
        self.items_weight = sum(
            obj.effective_weight for obj in self.contents if obj is not exclude
        )

    def at_pre_object_receive(self, arriving_object, source_location, **kwargs):
        """Refuse an object that has no weight and so cannot be carried.

        Returns:
            bool: ``False`` aborts the move and leaves the object where it was.
        """
        # The chain's answer first: returning True over another mixin's veto
        # would silently overrule it.
        if not super().at_pre_object_receive(
            arriving_object, source_location, **kwargs
        ):
            return False

        if not isinstance(arriving_object, EquipmentCarriableMixin):
            # An aborted move reports nothing to whoever attempted it, so the
            # reason is only ever going to be found here.
            equipment_log(
                f"{arriving_object} refused by {self}: no "
                f"EquipmentCarriableMixin, so it has no weight.",
                level="WARN",
            )
            return False

        return True

    def at_object_receive(self, moved_obj, source_location, move_type="move", **kwargs):
        """Rebuild the total; the object is already in ``contents``."""
        super().at_object_receive(
            moved_obj, source_location, move_type=move_type, **kwargs
        )
        self._recalculate_item_weight()

    def at_object_leave(self, moved_obj, target_location, move_type="move", **kwargs):
        """Rebuild the total, less the object that is on its way out."""
        super().at_object_leave(
            moved_obj, target_location, move_type=move_type, **kwargs
        )
        self._recalculate_item_weight(exclude=moved_obj)

    def at_init(self):
        """Rebuild the total whenever the carrier is loaded into memory.

        Drift that survived a shutdown is corrected the first time the object
        comes back, which is what makes the rebuild self-healing.
        """
        super().at_init()
        # at_init also fires on an object that is not yet saved, where reading
        # contents raises during queryset iteration.
        if not self.pk or getattr(self._state, "db", None) is None:
            return
        self._recalculate_item_weight()
