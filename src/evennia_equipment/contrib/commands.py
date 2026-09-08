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

from evennia_equipment.contrib.utils import match_slot, split_argument


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

        item_text, slot_text, named = split_argument(self.args, "on")

        slot = None
        if named:
            # Matched before wear() is called, so a mistyped slot never puts
            # the item on somewhere else first.
            slot, refusal = match_slot(caller, slot_text)
            if refusal:
                caller.msg(refusal)
                return

        worn, message = caller.wear(item_text, slot=slot)
        caller.msg(message)
        if not worn:
            return

        caller.location.msg_contents(
            f"$You() $conj(wear) {item_text}.",
            from_obj=caller,
            exclude=[caller],
        )


class CmdRemove(Command):
    """
    Take something off.

    Usage:
        remove <item>
        remove <item> from <slot>
        remove from <slot>

    Naming a slot is how you say which of two identical items you mean — the
    ring on your right hand rather than the one on your left. Type `equipment`
    to see the slots you have.
    """

    key = "remove"
    locks = "cmd:all()"
    help_category = "Items"

    def func(self):
        caller = self.caller
        args = self.args.strip()

        if not args:
            caller.msg("Remove what?")
            return

        # A leading "from" is the third form — a slot with no item — and the
        # padding in split_argument() is what makes it an ordinary split
        # rather than a case of its own.
        item_text, slot_text, named = split_argument(args, "from")

        slot = None
        if named:
            # Matched before remove() is called, so a mistyped slot never
            # strips something else first.
            slot, refusal = match_slot(caller, slot_text)
            if refusal:
                caller.msg(refusal)
                return

        removed, message = caller.remove(item_text or None, slot=slot)
        caller.msg(message)
        if not removed:
            return

        caller.location.msg_contents(
            f"$You() $conj(remove) {item_text or slot_text}.",
            from_obj=caller,
            exclude=[caller],
        )
