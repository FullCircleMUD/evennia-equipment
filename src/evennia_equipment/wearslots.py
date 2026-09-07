# SPDX-License-Identifier: BSD-3-Clause
"""EquipmentWearslotsMixin — a wearer with equipment slots.

A consumer writes one subclass per body plan, naming the slots that creature
has as members of the enum ``EQUIPMENT_WEARSLOTS`` points at::

    class HumanoidEquipmentMixin(EquipmentWearslotsMixin):
        body_slots = (WearSlot.HEAD, WearSlot.BODY, WearSlot.LEFT_HAND)

``body_slots`` is the declaration. ``worn_items`` is the storage — a real,
persisted dictionary of slot name to the item in it or ``None``, built once and
mutated from then on.

The declaration is checked when the subclass is defined, which is the earliest
the library can see it: nothing at boot can enumerate a consumer's typeclasses.

Wearslots extends carrying: anything with equipment slots also carries things,
and a game that wants slots does not get to opt out of weight.
"""

from enum import Enum

# Evennia, because AttributeProperty is Evennia's — a descriptor over its
# attribute handler, and the mechanism this library validates through. There is
# no engine-free equivalent to import instead.
from evennia.typeclasses.attributes import AttributeProperty
from evennia_targeting import f_key_matches, op_not, walk_contents

from evennia_equipment.carrying import EquipmentCarryingMixin
from evennia_equipment.targeting import f_identity_in, f_worn_by


class EquipmentWearslotsMixin(EquipmentCarryingMixin):
    """Gives a wearer the slots its body plan declares.

    Mix into anything that wears equipment — a character, a mob, a mount.
    """

    #: The slots this creature has, as members of the consumer's slot enum.
    #: Empty on the base; every subclass names its own.
    body_slots = ()

    #: Storage. Read through ``worn_items``, which builds it if it is absent.
    _worn_items = AttributeProperty(None)

    #: The identities of what is worn, written down so it can be restored
    #: after a world rebuild. Persisted, never ndb: it has to survive the very
    #: event that destroys everything else about the wearer's equipment.
    worn_equipment_record = AttributeProperty(set)

    @property
    def worn_items(self):
        """Slot name to the item in it, or ``None``.

        Built on first read if it is not there. ``at_init()`` is the usual
        place, but it fires on load and an object can be reached without
        having been loaded — held in Evennia's idmapper cache across a
        rollback, most obviously. A read that could return ``None`` would put
        that on every caller.
        """
        if not self._worn_items:
            self._worn_items = {slot.value: None for slot in self.body_slots}
        return self._worn_items

    @worn_items.setter
    def worn_items(self, value):
        self._worn_items = value

    def __init_subclass__(cls, **kwargs):
        """Refuse a body plan the consumer cannot have meant.

        Runs when the subclass is defined, so a mistake is reported against
        the class that made it rather than surfacing later as a wearer with
        the wrong slots. Does not run for this class itself, which is why the
        base is allowed to declare nothing.
        """
        super().__init_subclass__(**kwargs)

        from evennia_equipment.config import SETTING_WEARSLOTS, valid_slot_names

        slots = cls.body_slots
        if not slots:
            raise AttributeError(
                f"{cls.__name__} carries EquipmentWearslotsMixin but declares "
                f"no body_slots. Name the slots this creature has, as members "
                f"of the enum {SETTING_WEARSLOTS} points at — "
                f"body_slots = (WearSlot.HEAD, WearSlot.BODY)."
            )

        not_members = [slot for slot in slots if not isinstance(slot, Enum)]
        if not_members:
            raise AttributeError(
                f"{cls.__name__} declares {not_members!r} in body_slots, which "
                f"are not enum members. Name them through the enum — "
                f"WearSlot.HEAD rather than 'HEAD' — so a typo is caught here "
                f"rather than at the first wear."
            )

        names = [slot.value for slot in slots]
        repeated = sorted({name for name in names if names.count(name) > 1})
        if repeated:
            raise AttributeError(
                f"{cls.__name__} names {', '.join(repeated)} more than once in "
                f"body_slots. A slot is one place on the creature, so the "
                f"repeat would silently give it fewer slots than it reads."
            )

        known = valid_slot_names()
        unknown = sorted(name for name in names if name not in known)
        if unknown:
            raise AttributeError(
                f"{cls.__name__} names {', '.join(unknown)} in body_slots, "
                f"which the slot enum does not hold. Add it to the enum named "
                f"by {SETTING_WEARSLOTS}, or correct the spelling."
            )

    def at_init(self):
        """Build the slot dictionary, or bring it into line with the class.

        Once per load rather than on every read. Fires on every load, which is
        what covers an object created before the mixin was added — that
        object's ``at_object_creation`` has already run and never will again.
        """
        super().at_init()

        # at_init also fires on an object that is not yet saved, where reading
        # or writing attributes raises.
        if not self.pk or getattr(self._state, "db", None) is None:
            return

        declared = [slot.value for slot in self.body_slots]

        if set(declared) == set(self.worn_items):
            return

        # Rebuilt in declared order, keeping what each surviving slot holds.
        # Assignments are carried across rather than reset: a slot added must
        # not cost the wearer everything else it had on.
        #
        # An item in a dropped slot needs no moving. Wearing never took it out
        # of contents, so ceasing to be worn leaves it exactly where it is.
        self.worn_items = {
            name: self.worn_items.get(name) for name in declared
        }

    def is_worn(self, item) -> bool:
        """Whether this item currently occupies any of this wearer's slots.

        Identity, not equality. A consumer's typeclass may compare by key or
        by token id, and ``in`` would then report a second, identical item as
        already worn.
        """
        return any(held is item for held in (self.worn_items or {}).values())

    def _occupied_ids(self) -> set:
        """Return the identities of the items currently in slots.

        Identity rather than the objects themselves: a set membership test
        uses ``__hash__`` and ``__eq__``, and a consumer's typeclass may
        define either. Evennia's idmapper gives one instance per row, so
        ``id()`` is stable for as long as anything holds a reference.
        """
        # `is not None`, not truthiness: a consumer's typeclass may define
        # __bool__ or __len__ — an empty container reads as falsy — and a
        # worn one would then be skipped and show up in the inventory.
        return {
            id(held)
            for held in (self.worn_items or {}).values()
            if held is not None
        }

    def get_all_worn(self):
        """Return the items this wearer has on, each once.

        Built from ``contents`` rather than from the slot dictionary, which can
        hold an object that no longer exists — ``delete()`` fires no hook, so
        nothing clears it. An answer assembled from ``contents`` cannot return
        a ghost.

        Returns:
            list: The worn items, in the order ``contents`` gives them.
        """
        return walk_contents(self, self, f_worn_by(self))

    def get_carried(self):
        """Return what is held but not worn — what a player calls inventory.

        Returns:
            list: Everything in ``contents`` that is not in a slot.
        """
        return walk_contents(self, self, op_not(f_worn_by(self)))

    def _resolve_wearable(self, text):
        """Find the item ``text`` names among the things this wearer holds.

        Two ordered passes, because that is what makes the refusals accurate.
        A single pass over the unworn items tells someone already wearing the
        helmet that they are not carrying it, which is both false and useless.

        Args:
            text (str): What the player typed.

        Returns:
            tuple: ``(item, None)`` when one item is the answer, or
            ``(None, refusal)`` when none is.
        """
        name = f_key_matches(text)

        carried = walk_contents(self, self, op_not(f_worn_by(self)), name)
        if carried:
            # Items sharing a key are interchangeable, so the first is the
            # answer. Differing keys are a real question — and it echoes what
            # was typed rather than listing candidates, which could be five.
            if len({obj.key.lower() for obj in carried}) > 1:
                return (None, f"Which {text} do you mean?")
            return (carried[0], None)

        worn = walk_contents(self, self, f_worn_by(self), name)
        if worn:
            return (None, f"You are already wearing {worn[0]}.")

        return (None, f"You are not carrying {text}.")

    def wear(self, item):
        """Put an item into the first group of slots that will take it.

        Takes a string or an object. A string is resolved against what this
        wearer holds — otherwise a command has to filter the contents to find
        an object, only to hand it to a method that filters again to confirm
        what the caller just established. An object is still accepted, because
        ``restore_worn()`` and a consumer equipping something it has just made
        both hold one, and two identical rings are distinct objects but the
        same string.

        Args:
            item (Object or str): The object to wear, or what the player typed.

        Returns:
            tuple: ``(bool, str)`` — whether it was worn, and why not if it was
            not. The mixin answers; the command speaks.
        """
        if isinstance(item, str):
            resolved, refusal = self._resolve_wearable(item)
            if resolved is None:
                return (False, refusal)
            item = resolved

        if item not in self.contents:
            return (False, f"You are not carrying {item}.")

        if self.is_worn(item):
            return (False, f"You are already wearing {item}.")

        groups = getattr(item, "wearslot", None)
        if not groups:
            return (False, f"{item} is not something you can wear.")

        slots = self.worn_items or {}

        # Choose before writing anything. Filling slots as they are checked
        # would leave a two-handed item in one hand when the other turns out
        # to be occupied.
        for group in groups:
            if all(slot in slots and slots[slot] is None for slot in group):
                worn = dict(slots)
                worn.update({slot: item for slot in group})
                self.worn_items = worn
                return (True, f"You wear {item}.")

        return (False, f"You have nowhere to wear {item}.")

    def update_worn_equipment_record(self):
        """Write down the identities of what this wearer currently has on.

        Rebuilt rather than added to, so the record describes the present: an
        item taken off since the last call is not in it. An append-only version
        would slowly accumulate gear the wearer no longer owns, which restore
        would then look for and never find.

        A consumer calls this before archiving. There is no way for the library
        to know when that is, and nothing it could hook without learning that
        archiving exists.

        Items with no identity are skipped — there is nothing to match them by,
        so recording anything would invent a key restore could never resolve.
        """
        self.worn_equipment_record = {
            identity
            for identity in (item.wearslot_identity for item in self.get_all_worn())
            if identity is not None
        }

    def restore_worn(self):
        """Put back on whatever the record says was worn.

        A consumer calls this after their own restore has returned the items to
        ``contents``. The library cannot know when that is, and an item not yet
        back is simply not seen.

        Walks ``contents`` rather than the record, so an identity matching
        nothing is never visited and needs no handling of its own. Order does
        not matter: the items all fitted at once when the record was written,
        so they fit now in whatever order ``contents`` gives them.

        Returns:
            list: One ``(bool, str)`` per item attempted, straight from
            ``wear()``. A refusal is the only diagnostic a consumer gets, and
            it is the one that says a slot has gone or the identity attribute
            names something the items do not carry.
        """
        record = self.worn_equipment_record or set()
        return [
            self.wear(item)
            for item in walk_contents(self, self, f_identity_in(record))
        ]

    def at_pre_remove(self, item):
        """Whether this item may come off. Override to refuse.

        The library refuses nothing of its own. A consumer overrides this for
        a cursed item, a paralysed wearer, a rule about combat — whatever
        their game holds.

        On the wearer rather than the item, deliberately. A curse is the
        item's business, but "you are paralysed" is the wearer's, and an
        item-side hook could not express it. A consumer wanting item-side
        logic delegates to the item in one line; the reverse is not available.

        Args:
            item (Object): The object about to come off.

        Returns:
            tuple: ``(bool, str)`` — the same shape ``remove()`` returns, so a
            consumer's reason reaches the player rather than being replaced by
            something generic.
        """
        return (True, "")

    def remove(self, item):
        """Free every slot an item occupies, leaving it in ``contents``.

        Taking something off does not put it down.

        Args:
            item (Object): The object to take off.

        Returns:
            tuple: ``(bool, str)`` — whether it came off, and why not if it
            did not.
        """
        worn = self.worn_items or {}
        if not self.is_worn(item):
            return (False, f"You are not wearing {item}.")

        allowed, refusal = self.at_pre_remove(item)
        if not allowed:
            return (False, refusal)

        # Every slot holding it, not the first one found: a two-handed item
        # sits under two keys, and freeing one leaves a phantom in the other.
        #
        # `is`, not `==`: a consumer's typeclass may compare by key or by token
        # id, and equality would then free every slot holding something that
        # merely looks the same.
        self.worn_items = {
            slot: (None if held is item else held) for slot, held in worn.items()
        }
        return (True, f"You remove {item}.")
