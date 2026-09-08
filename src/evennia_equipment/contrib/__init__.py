# SPDX-License-Identifier: BSD-3-Clause
"""Optional commands, for a game that wants a working set rather than its own.

Nothing here is imported by the library itself, and a consumer driving the
mixins from their own code never installs it. What it provides is the vocabulary
Evennia has no word for — wearing, removing, and reading a slot sheet.

These are meant to be **read and replaced**, not configured. There is one seam,
``CmdInventory.extra_lines()``, and it exists because a game's balances sit
between the items and the summary — a position no override of the rendering
could reach. Everything else you want different, you get by overriding
``func()``, which is what almost every game will do: the interesting parts of an
inventory listing are the parts only that game knows about.
"""

from evennia_equipment.contrib.cmdset import EquipmentCmdSet
from evennia_equipment.contrib.commands import (
    CmdEquipment,
    CmdInventory,
    CmdRemove,
    CmdWear,
)

__all__ = [
    "CmdEquipment",
    "CmdInventory",
    "CmdRemove",
    "CmdWear",
    "EquipmentCmdSet",
]
