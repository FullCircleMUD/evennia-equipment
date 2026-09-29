# SPDX-License-Identifier: BSD-3-Clause
"""Optional commands, for a game that wants a working set rather than its own.

Nothing here is imported by the library itself, and a consumer driving the
mixins from their own code never installs it.

Each command comes as a mixin — ``CmdWearMixin``, ``CmdRemoveMixin``,
``CmdEquipmentMixin``, ``CmdInventoryMixin`` — for a game to compose onto its
own command class, and as a concrete command over Evennia's ``Command``,
collected in ``EquipmentCmdSet``. The seams are ``announce()`` and
``at_success()`` on wearing and removing, ``extra_lines()`` on the inventory,
and ``slot_column_gap`` on the slot sheet.
"""

from evennia_equipment.contrib.cmdset import EquipmentCmdSet
from evennia_equipment.contrib.commands import (
    CmdEquipment,
    CmdEquipmentMixin,
    CmdInventory,
    CmdInventoryMixin,
    CmdRemove,
    CmdRemoveMixin,
    CmdWear,
    CmdWearMixin,
)

__all__ = [
    "CmdEquipment",
    "CmdEquipmentMixin",
    "CmdInventory",
    "CmdInventoryMixin",
    "CmdRemove",
    "CmdRemoveMixin",
    "CmdWear",
    "CmdWearMixin",
    "EquipmentCmdSet",
]
