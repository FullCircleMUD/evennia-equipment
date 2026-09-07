# SPDX-License-Identifier: BSD-3-Clause
"""EquipmentWearslotsMixin — a wearer with equipment slots.

A typeclass names which layout it uses; the mixin derives its slots from the
layouts the consumer declared in ``EQUIPMENT_WEARSLOTS``::

    class Character(EquipmentWearslotsMixin, DefaultCharacter):
        wearslot_layout = "humanoid"

**The slot names are not persisted.** Only what is occupied is stored, and the
full set of slots is read from the layout every time. A slot added to a layout
then appears on characters that already exist, rather than being unusable
because their dictionary was built before it was declared.

Wearslots extends carrying: anything with equipment slots also carries things,
and a game that wants slots does not get to opt out of weight.
"""

from evennia_equipment.carrying import EquipmentCarryingMixin


class EquipmentWearslotsMixin(EquipmentCarryingMixin):
    """Gives a wearer the slots its layout declares.

    Mix into anything that wears equipment — a character, a mob, a mount.
    """

    #: Which of the consumer's declared layouts this typeclass uses. Named
    #: rather than inlined so a game states each body plan once.
    wearslot_layout = None

    @property
    def wearslots(self):
        """Return every slot this wearer has, mapped to what fills it.

        Derived from the layout on every read, so the slots follow the
        consumer's declaration rather than a copy taken when the object was
        created.

        Returns:
            dict: slot name to the item in it, or ``None``.

        Raises:
            AttributeError: If no layout is declared, or the declared name is
                not one of the consumer's layouts.
        """
        from evennia_equipment.config import SETTING_WEARSLOTS, get_wearslot_layouts

        if not self.wearslot_layout:
            raise AttributeError(
                f"{type(self).__name__} carries EquipmentWearslotsMixin but "
                f"declares no wearslot_layout. Name one of the layouts in "
                f"{SETTING_WEARSLOTS}, e.g. wearslot_layout = 'humanoid'."
            )

        layouts = get_wearslot_layouts()
        if self.wearslot_layout not in layouts:
            raise AttributeError(
                f"{type(self).__name__} names the layout "
                f"{self.wearslot_layout!r}, which {SETTING_WEARSLOTS} does not "
                f"declare. Declared layouts are: "
                f"{', '.join(sorted(layouts)) or 'none'}."
            )

        # Only what is occupied is stored; the slots themselves come from the
        # layout every read, so a slot added later is immediately usable.
        worn = self.db.worn_slots or {}
        return {slot: worn.get(slot) for slot in layouts[self.wearslot_layout]}

    def is_worn(self, item) -> bool:
        """Whether this item currently occupies any of this wearer's slots."""
        return item in (self.db.worn_slots or {}).values()

    def get_all_worn(self):
        """Return the items this wearer has on, each once.

        Built from ``contents`` rather than from the slot map, which can hold
        an object that no longer exists — ``delete()`` fires no hook, so
        nothing clears it. An answer assembled from ``contents`` cannot return
        a ghost.

        Returns:
            list: The worn items, in the order ``contents`` gives them.
        """
        # Walking contents rather than the slot map is what deduplicates a
        # multi-slot item as well: it appears once here however many slots it
        # fills.
        occupied = set((self.db.worn_slots or {}).values())
        return [obj for obj in self.contents if obj in occupied]

    def get_carried(self):
        """Return what is held but not worn — what a player calls inventory.

        Returns:
            list: Everything in ``contents`` that is not in a slot.
        """
        occupied = set((self.db.worn_slots or {}).values())
        return [obj for obj in self.contents if obj not in occupied]

    def wear(self, item):
        """Put an item into the first group of slots that will take it.

        The item is expected to be in ``contents`` already — finding the object
        a player named is the command layer's job, and resolving names here
        would mean depending on a targeting system.

        Args:
            item (Object): The object to wear. Already in hand.

        Returns:
            tuple: ``(bool, str)`` — whether it was worn, and why not if it was
            not. The mixin answers; the command speaks.
        """
        if item not in self.contents:
            return (False, f"You are not carrying {item}.")

        if self.is_worn(item):
            return (False, f"You are already wearing {item}.")

        groups = getattr(item, "wearslot", None)
        if not groups:
            return (False, f"{item} is not something you can wear.")

        slots = self.wearslots

        # Choose before writing anything. Filling slots as they are checked
        # would leave a two-handed item in one hand when the other turns out
        # to be occupied.
        for group in groups:
            if all(slot in slots and slots[slot] is None for slot in group):
                worn = dict(self.db.worn_slots or {})
                worn.update({slot: item for slot in group})
                self.db.worn_slots = worn
                return (True, f"You wear {item}.")

        return (False, f"You have nowhere to wear {item}.")

    def remove(self, item):
        """Free every slot an item occupies, leaving it in ``contents``.

        Taking something off does not put it down. Nothing refuses — see the
        open question about cursed items in the test plan.

        Args:
            item (Object): The object to take off.

        Returns:
            tuple: ``(bool, str)`` — whether it came off, and why not if it
            did not.
        """
        worn = self.db.worn_slots or {}
        if item not in worn.values():
            return (False, f"You are not wearing {item}.")

        # Every slot holding it, not the first one found: a two-handed item
        # sits under two keys, and freeing one leaves a phantom in the other.
        self.db.worn_slots = {
            slot: held for slot, held in worn.items() if held != item
        }
        return (True, f"You remove {item}.")
