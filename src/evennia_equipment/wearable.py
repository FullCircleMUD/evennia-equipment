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

# Evennia, because AttributeProperty is Evennia's — a descriptor over its
# attribute handler, and the mechanism this library validates through. There is
# no engine-free equivalent to import instead.
from evennia.typeclasses.attributes import AttributeProperty

from evennia_equipment.carriable import EquipmentCarriableMixin


class WearslotProperty(AttributeProperty):
    """A slot declaration, checked for shape and for names that exist.

    Two checks, both here. The format, and whether every name is in the
    declared slot enum — an item does not know which creature will wear it, so
    the enum is as far as it can go.
    """

    def at_set(self, value, obj):
        """Return the declaration unchanged, or refuse it.

        Args:
            value (any): The declaration about to be stored.
            obj (object): The object the attribute is attached to.

        Returns:
            list: The validated declaration.

        Raises:
            AttributeError: If the shape is wrong, or a slot name is not in
                the declared slot enum.
        """
        from evennia_equipment.config import valid_slot_names

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

        known = valid_slot_names()

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
                    f"{self._key} names {', '.join(unknown)}, which the slot "
                    f"enum does not hold. Add it to the enum named by "
                    f"EQUIPMENT_WEARSLOTS, or correct the spelling."
                )

        return value


class EquipmentWearableMixin(EquipmentCarriableMixin):
    """Gives an item a slot declaration on top of its weight.

    Mix into anything that can be worn or wielded. Consumers declare the slots
    per item type, re-declaring it as a ``WearslotProperty`` so the checks
    survive.
    """

    wearslot = WearslotProperty(None)

    @property
    def wearslot_identity(self):
        """What this item is known by across a world rebuild, or ``None``.

        Read from the attribute ``EQUIPMENT_IDENTITY_ATTRIBUTE`` names — a
        token id, an archive id, whatever the game already uses to identify an
        item permanently. A database key cannot serve: a rebuild reissues every
        one of them, which is the situation this exists for.

        ``None`` is not a failure. An item without the attribute is worn
        perfectly well and simply cannot be restored, because there is nothing
        to match it by. Inventing a key would be worse — restore would look for
        something that never existed.

        A game whose items are not uniform overrides this instead of using the
        setting.
        """
        from evennia_equipment.config import get_identity_attribute

        return getattr(self, get_identity_attribute(), None)
