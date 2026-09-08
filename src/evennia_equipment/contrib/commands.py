# SPDX-License-Identifier: BSD-3-Clause
"""The commands a player types.

Each one parses, speaks and broadcasts, and nothing else. Resolving an item,
choosing slots and deciding what to say are the mixin's, so a refusal reads the
same however a player reached it.
"""

# Evennia, because a command is Evennia's — these subclass its Command and are
# merged into a cmdset. Nothing in contrib runs without an engine, which is part
# of why it is separate from core.
from evennia import Command

from evennia_equipment.contrib.utils import match_slot


class CmdWear(Command):
    """
    Put something on.

    Usage:
        wear <item>
        wear <item> on <slot>

    Naming a slot overrides where the item would go by default — useful when
    something can be worn in more than one place. Type `equipment` to see the
    slots you have.
    """

    key = "wear"
    locks = "cmd:all()"
    help_category = "Items"

    def func(self):
        caller = self.caller

        if not self.args.strip():
            caller.msg("Wear what?")
            return

        # rpartition, not partition: an item may contain the word — "a ring on
        # a chain" — and splitting on the first would take the chain for a slot.
        item_text, separator, slot_text = self.args.rpartition(" on ")
        if not separator:
            item_text, slot_text = self.args, ""

        slot = None
        if separator:
            # Matched before wear() is called, so a mistyped slot never puts
            # the item on somewhere else first.
            slot, refusal = match_slot(caller, slot_text)
            if refusal:
                caller.msg(refusal)
                return

        worn, message = caller.wear(item_text.strip(), slot=slot)
        caller.msg(message)
        if not worn:
            return

        caller.location.msg_contents(
            f"$You() $conj(wear) {item_text.strip()}.",
            from_obj=caller,
            exclude=[caller],
        )
