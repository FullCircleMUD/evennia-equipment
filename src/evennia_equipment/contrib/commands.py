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


class CmdEquipment(Command):
    """
    See what you are wearing.

    Usage:
        equipment
        eq

    Lists every slot your body has, in order, and what is in it. An empty slot
    shows its name and nothing else.
    """

    key = "equipment"
    aliases = ["eq"]
    locks = "cmd:all()"
    help_category = "Items"

    # Spaces between the slot column and the item name. A class attribute
    # rather than a module constant, so a game widens it by subclassing.
    slot_column_gap = 2

    def func(self):
        caller = self.caller
        slots = caller.worn_items or {}

        names = {slot: slot.replace("_", " ").title() for slot in slots}
        # Computed rather than fixed, so a body plan naming a
        # LEFT_SHOULDER_PAULDRON still lines up. The brackets are part of the
        # column, hence the two.
        width = max((len(name) for name in names.values()), default=0) + 2

        lines = ["|wEquipped Items|n", ""]
        for slot, item in slots.items():
            bracket = f"<|c{names[slot]}|n>"
            if item is None:
                # The absence is the information. A word for it would be noise
                # on every line a player has not filled.
                lines.append(f"  {bracket}")
                continue
            # Evennia's own viewer-aware hook, so a game with darkness gets
            # this listing right without a seam of ours.
            pad = " " * (width - len(names[slot]) - 2 + self.slot_column_gap)
            lines.append(f"  {bracket}{pad}|w{item.get_display_name(caller)}|n")

        caller.msg("\n".join(lines))
