# SPDX-License-Identifier: BSD-3-Clause
"""The four commands as one thing to merge.

A convenience rather than a requirement: a game wanting three of them adds
those individually, and one replacing ``inventory`` adds its own after ours.
"""

# Evennia, because a cmdset is Evennia's — this subclasses its CmdSet and is
# merged by its command handler. Nothing in contrib runs without an engine.
from evennia import CmdSet

from evennia_equipment.contrib.commands import (
    CmdEquipment,
    CmdInventory,
    CmdRemove,
    CmdWear,
)


class EquipmentCmdSet(CmdSet):
    """Wearing, removing, and reading what you have on and what you carry.

    Merge it into the cmdset a game already has::

        class CharacterCmdSet(default_cmds.CharacterCmdSet):
            def at_cmdset_creation(self):
                super().at_cmdset_creation()
                self.add(EquipmentCmdSet)

    Added after the defaults, so ``inventory`` replaces Evennia's rather than
    competing with it — merging is by key, and the later set wins.
    """

    key = "equipment"

    def at_cmdset_creation(self):
        self.add(CmdWear())
        self.add(CmdRemove())
        self.add(CmdEquipment())
        self.add(CmdInventory())
