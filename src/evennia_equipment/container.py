# SPDX-License-Identifier: BSD-3-Clause
"""EquipmentContainerMixin — an object that is carried and carrying at once.

A backpack has its own weight and holds things, so it takes both mixins. It
adds two behaviours on top: it contributes what is inside it as well as
itself, and it tells its own holder when that total changes.

Neither half needs changing to accommodate it. A carrier sums
``effective_weight``, which a container answers for itself, so nothing in
``EquipmentCarryingMixin`` knows what a container is.
"""

from evennia_equipment.carriable import EquipmentCarriableMixin
from evennia_equipment.carrying import EquipmentCarryingMixin


class EquipmentContainerMixin(EquipmentCarriableMixin, EquipmentCarryingMixin):
    """Gives an object its own weight and a total of what it holds.

    Mix into a backpack, a chest, a saddlebag. A container whose contents
    should *not* count against whoever carries it overrides
    ``effective_weight`` to return ``self.weight`` alone.
    """

    @property
    def effective_weight(self):
        """Its own weight plus everything inside it.

        ``current_weight_carried`` rather than ``items_weight``, so a
        container whose game tracks a balance — coin in a purse — contributes
        that too, through ``extra_weight()``.
        """
        return self.weight + self.current_weight_carried

    def describe_container(self, unit=None):
        """What it holds against what it takes, as a line a player reads.

        ::

            sack.describe_container("kg")   # ["Holds: 12 of 30 kg"]

        Each number in its shortest form, as ``describe_weight`` writes one,
        and a unit given follows the last of them. A container with no limit
        says so in place of a capacity. See HD.
        """
        suffix = f" {unit}" if unit else ""
        carried = f"{self.current_weight_carried:g}"
        capacity = self.effective_capacity
        if capacity == float("inf"):
            return [f"Holds: {carried}{suffix}, no limit"]
        return [f"Holds: {carried} of {capacity:g}{suffix}"]

    def _recalculate_item_weight(self, exclude=None):
        """Rebuild, then tell whoever holds this that its total changed.

        A container's ``effective_weight`` moves whenever its contents do, so
        the holder's total is stale until it hears about it. The walk upward
        ends on its own: a character is not carriable and a room does not
        carry, so neither passes the check in ``at_weight_changed()``.
        """
        super()._recalculate_item_weight(exclude=exclude)
        self.at_weight_changed()
