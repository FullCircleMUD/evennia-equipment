# SPDX-License-Identifier: BSD-3-Clause
"""The commands a player types.

``wear`` and ``remove`` come as mixins — ``CmdWearMixin`` and
``CmdRemoveMixin`` — for a game to compose onto its own command class, and as
``CmdWear`` and ``CmdRemove``, the same mixins over Evennia's ``Command``, for
``EquipmentCmdSet``. Each decides in the command and hands the method an item
it has already found: ``resolve_wear()`` and ``resolve_remove()`` do the
finding, and ``wear()`` and ``remove()`` only execute, with their hooks.

``equipment`` and ``inventory`` come the same way — ``CmdEquipmentMixin`` and
``CmdInventoryMixin``, and ``CmdEquipment`` and ``CmdInventory`` over Evennia's
``Command``.
"""

# Evennia, because a command is Evennia's — these subclass its Command and are
# merged into a cmdset. Nothing in contrib runs without an engine, which is part
# of why it is separate from core.
from evennia import Command
from evennia_targeting import bucket_contents, op_not

from evennia_equipment.contrib.utils import resolve_remove, resolve_wear
from evennia_equipment.finders import find_carried
from evennia_equipment.targeting import f_worn_by


def _slot_name(slot):
    """A slot member as a player reads it — ``LEFT_HAND`` as ``left hand``."""
    return slot.value.replace("_", " ").lower()


class _EquipmentVerbMixin:
    """The two seams ``wear`` and ``remove`` share. Both run only on success."""

    #: The verb the room line conjugates.
    verb = ""

    def announce(self, item):
        """Tell the room. Override for a game's own messaging. See CW-14.

        Args:
            item (Object): What went on or came off.
        """
        caller = self.caller
        caller.location.msg_contents(
            f"$You() $conj({self.verb}) {{item}}.",
            from_obj=caller,
            exclude=[caller],
            mapping={"item": item},
        )

    def at_success(self, item):
        """Called once the item has gone on or come off. Does nothing here.

        Where a game whose equipping costs a turn in a fight starts its time
        wait. See CW-15.

        Args:
            item (Object): What went on or came off.
        """


class CmdWearMixin(_EquipmentVerbMixin):
    """Put something on: find it, check it can go where asked, wear it.

    ``slot`` and ``verb`` are what a game sets to make ``wield`` or ``hold``
    of it. See CW-17 and CW-18.
    """

    verb = "wear"

    #: An enum member fixing where the item goes. With it set, the argument is
    #: the item alone — ``on`` is part of a name, not a split.
    slot = None

    def func(self):
        caller = self.caller
        verb = self.verb
        text = self.args.strip()
        if not text:
            caller.msg(f"{verb.capitalize()} what?")
            return

        if self.slot is None:
            answer, refusal = resolve_wear(caller, text)
            if refusal:
                caller.msg(refusal)
                return
            item, slot = answer
        else:
            item, refusal = find_carried(caller, text)
            if refusal:
                caller.msg(refusal)
                return
            slot = self.slot
        name = item.get_display_name(caller)

        if caller.slots_for(item, slot) is None:
            groups = getattr(item, "wearslot", None)
            if not groups:
                caller.msg(f"{name} is not something you can {verb}.")
            elif slot is not None and not any(slot.value in group for group in groups):
                # No group holds the slot at all, which is not the same as the
                # slot being taken. See CW-19 and CW-20.
                if self.slot is None:
                    caller.msg(f"{name} can't go on your {_slot_name(slot)}.")
                else:
                    caller.msg(f"You can't {verb} {name}.")
            else:
                caller.msg(f"You have nowhere to {verb} {name}.")
            return

        worn, reason = caller.wear(item, slot)
        if not worn:
            caller.msg(reason)
            return

        caller.msg(f"You {verb} {name}.")
        self.announce(item)
        self.at_success(item)


class CmdRemoveMixin(_EquipmentVerbMixin):
    """Take something off: find it, by name or by slot, and remove it."""

    verb = "remove"

    def func(self):
        caller = self.caller
        text = self.args.strip()
        if not text:
            caller.msg("Remove what?")
            return

        item, refusal = resolve_remove(caller, text)
        if refusal:
            caller.msg(refusal)
            return

        removed, reason = caller.remove(item)
        if not removed:
            caller.msg(reason)
            return

        caller.msg(f"You remove {item.get_display_name(caller)}.")
        self.announce(item)
        self.at_success(item)


class CmdWear(CmdWearMixin, Command):
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


class CmdRemove(CmdRemoveMixin, Command):
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


class CmdEquipmentMixin:
    """Every slot the caller has, in body-plan order, and what is in it."""

    # Spaces between the slot column and the item name. A class attribute
    # rather than a module constant, so a game widens it by subclassing.
    slot_column_gap = 2

    def func(self):
        caller = self.caller
        slots = caller.worn_items

        names = {slot: slot.replace("_", " ").title() for slot in slots}
        # Computed rather than fixed, so a body plan naming a
        # LEFT_SHOULDER_PAULDRON still lines up.
        longest = max((len(name) for name in names.values()), default=0)

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
            pad = " " * (longest - len(names[slot]) + self.slot_column_gap)
            lines.append(f"  {bracket}{pad}|w{item.get_display_name(caller)}|n")

        caller.msg("\n".join(lines))


class CmdInventoryMixin:
    """What the caller carries and is not wearing, then what it all weighs."""

    def extra_lines(self):
        """Lines to show between the items and the carrying summary.

        Empty here, and the one seam the listing has. A game's currency and
        resource balances are more things being carried rather than a footer
        after them, so they belong above the line that totals what is carried.

        Returns:
            list: Strings, already formatted. Empty by default.
        """
        return []

    def func(self):
        caller = self.caller

        # One walk that filters out what is worn and groups the rest. Grouped
        # by key, not by what is shown: two different things a looker makes
        # out the same must stay two lines. See CI-05.
        groups = bucket_contents(caller, caller, _stack_key, op_not(f_worn_by(caller)))

        items = []
        for group in groups.values():
            name = group[0].get_display_name(caller)
            count = len(group)
            items.append(f"  {name} ({count})" if count > 1 else f"  {name}")

        lines = ["|wInventory:|n", ""]
        lines.extend(items or ["  You are not carrying anything."])

        extra = self.extra_lines()
        if extra:
            lines.append("")
            lines.extend(extra)

        carried = caller.current_weight_carried
        capacity = caller.effective_capacity
        lines.append("")
        # Unlimited is the default, so naming it would read as "of inf".
        if capacity == float("inf"):
            lines.append(f"Carrying {carried:.1f}.")
        else:
            lines.append(f"Carrying {carried:.1f} of {capacity:.1f}.")

        caller.msg("\n".join(lines))


def _stack_key(item, caller):  # noqa: ARG001
    """A stackable item's bucket is its key; an unstackable one gets its own.

    ``stackable`` is ``True`` unless the item says otherwise. See CI-03 and
    CI-13.
    """
    if getattr(item, "stackable", True):
        return item.key
    return id(item)


class CmdEquipment(CmdEquipmentMixin, Command):
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


class CmdInventory(CmdInventoryMixin, Command):
    """
    See what you are carrying.

    Usage:
        inventory
        inv
        i

    Lists what you hold but are not wearing, and what it all weighs. Type
    `equipment` for what you have on.
    """

    key = "inventory"
    aliases = ["inv", "i"]
    locks = "cmd:all()"
    help_category = "Items"
