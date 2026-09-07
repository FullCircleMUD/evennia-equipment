# SPDX-License-Identifier: BSD-3-Clause
"""EquipmentWearableMixin — an item that occupies slots on whoever wears it.

An item declares its slots as a **list of groups**. Each group is one option,
and every slot inside a group is taken together::

    wearslot = [["HEAD"]]                            # a helm
    wearslot = [["LEFT_FINGER"], ["RIGHT_FINGER"]]   # a ring — either finger
    wearslot = [["WIELD", "HOLD"]]                   # a greatsword — both hands
    wearslot = [["HEAD", "BODY", "LEGS"]]            # a suit of plate

The canonical form is required rather than normalised. A flat list is
ambiguous — ``["WIELD", "HOLD"]`` could mean either hand or both — so
converting one would invent a meaning rather than tidy a shape.

Wearable extends carriable: anything worn is also carried, and a game that
wants slots does not get to opt out of weight.
"""

from collections.abc import Sequence

from evennia.typeclasses.attributes import AttributeProperty

from evennia_equipment.carriable import EquipmentCarriableMixin


class WearslotProperty(AttributeProperty):
    """A slot declaration, checked for shape and for names that exist.

    Two checks, both here. The format, and whether every name appears in some
    declared layout — an item does not know which creature will wear it, so
    the union of every layout is as far as it can go.
    """

    def at_set(self, value, obj):
        """Return the declaration unchanged, or refuse it.

        Args:
            value (any): The declaration about to be stored.
            obj (object): The object the attribute is attached to.

        Returns:
            list: The validated declaration.

        Raises:
            AttributeError: If the shape is wrong, or a slot name appears in
                no declared layout.
        """
        from evennia_equipment.config import known_slot_names

        # Sequence rather than list: a class-level default is run through
        # from_pickle by _get_and_cache_default, which returns a _SaverList —
        # not a list subclass, so isinstance(value, list) is False for it.
        #
        # The string check comes first because str is a Sequence too, and one
        # is iterable with a length, so every test below would pass and leave
        # one letter per group.
        if isinstance(value, str) or not isinstance(value, Sequence):
            raise AttributeError(
                f"{self._key} is {value!r}. It must be a list of groups, each "
                f"group a list of slot names taken together — "
                f"[['WIELD', 'HOLD']] for both hands, "
                f"[['LEFT_FINGER'], ['RIGHT_FINGER']] for either."
            )

        if not value:
            raise AttributeError(
                f"{self._key} is empty. An item carrying the wearable mixin "
                f"occupies at least one slot; one that occupies none is not "
                f"wearable and does not need the mixin."
            )

        known = known_slot_names()

        for group in value:
            # The same string trap one level down: ['HEAD'] is a group, but
            # 'HEAD' as a group would be read as four single-letter slots.
            if isinstance(group, str) or not isinstance(group, Sequence):
                raise AttributeError(
                    f"{self._key} holds {group!r}, which is not a group. Every "
                    f"entry must be a list of slot names, so a single-slot item "
                    f"reads [['HEAD']] rather than ['HEAD']."
                )

            if not group:
                raise AttributeError(
                    f"{self._key} holds an empty group. A group is one way of "
                    f"wearing the item, so it names at least one slot."
                )

            not_strings = [slot for slot in group if not isinstance(slot, str)]
            if not_strings:
                raise AttributeError(
                    f"{self._key} holds {not_strings!r} in a group. Every slot "
                    f"name must be a string."
                )

            if len(set(group)) != len(group):
                repeated = sorted({slot for slot in group if group.count(slot) > 1})
                raise AttributeError(
                    f"{self._key} names {', '.join(repeated)} twice in one "
                    f"group. A group cannot occupy the same slot twice."
                )

            unknown = sorted(slot for slot in group if slot not in known)
            if unknown:
                raise AttributeError(
                    f"{self._key} names {', '.join(unknown)}, which no declared "
                    f"layout holds. Add the slot to a layout in "
                    f"EQUIPMENT_WEARSLOTS first, or correct the spelling."
                )

        return value


class EquipmentWearableMixin(EquipmentCarriableMixin):
    """Gives an item a slot declaration on top of its weight.

    Mix into anything that can be worn or wielded. Consumers declare the slots
    per item type, re-declaring it as a ``WearslotProperty`` so the checks
    survive.
    """

    wearslot = WearslotProperty(None)
