# SPDX-License-Identifier: BSD-3-Clause
"""EquipmentCarriableMixin — an object with a weight, which can be carried.

The root of the library: every other mixin sits downstream of this one, so
the type and range of ``weight`` is pinned tightly. It is a number — ``int``
or ``float`` — greater than or equal to zero, coerced to ``float`` on the way
in so one type always reads back out.

The check lives in ``at_set()`` rather than at each call site, so it runs once
wherever the value came from and fails at the assignment that caused it. See
``library-standards.md`` § Reading and writing object state, including the
limit: ``at_set()`` fires only on assignment through the descriptor, so
``obj.db.weight`` stores whatever it is given. That is documented rather than
defended against — it cannot be closed from here.
"""

# Evennia, because AttributeProperty is Evennia's — a descriptor over its
# attribute handler, and the mechanism this library validates through. There is
# no engine-free equivalent to import instead.
from evennia.typeclasses.attributes import AttributeProperty


class NonNegativeNumberProperty(AttributeProperty):
    """An ``AttributeProperty`` accepting only a number of zero or more.

    Booleans are refused rather than treated as numbers: ``bool`` subclasses
    ``int`` in Python, so ``isinstance(True, int)`` is ``True`` and a plain
    numeric check would store ``True`` as ``1.0`` without complaint.
    """

    def at_set(self, value, obj):
        """Return ``value`` as a float, or refuse it.

        Args:
            value (any): The value about to be stored.
            obj (object): The object the attribute is attached to.

        Returns:
            float: The validated value.

        Raises:
            AttributeError: If the value is not a number, or is negative.
        """
        # ``bool`` is checked before ``int`` because it subclasses it, so
        # ``isinstance(True, int)`` is True and ``True`` would store as 1.0.
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise AttributeError(
                f"{self._key} must be a number, not {value!r}."
            )
        if value < 0:
            raise AttributeError(
                f"{self._key} must be zero or more, not {value!r}."
            )
        return float(value)


class WeightProperty(NonNegativeNumberProperty):
    """A weight, which tells whoever is holding the object when it changes.

    The notification is here rather than in ``at_set()`` because ``at_set()``
    runs *before* the value is stored — a rebuild triggered from there would
    read this object's old weight back out.
    """

    def __set__(self, instance, value):
        super().__set__(instance, value)
        instance.at_weight_changed()


class EquipmentCarriableMixin:
    """Gives an object a weight, and nothing else.

    Mix into anything a character can pick up. Consumers override the default
    per item type, the way a game gives a dagger 0.5 and a greatsword 4.5 —
    re-declaring it as a ``WeightProperty``, so the notification survives.
    """

    weight = WeightProperty(0.0)

    @property
    def effective_weight(self):
        """What this object contributes to whoever is holding it.

        Its own weight, for anything that holds nothing. A container overrides
        this to add what is inside it, so a carrier never has to know what a
        container is.
        """
        return self.weight

    def at_weight_changed(self):
        """Tell whoever is holding this object to rebuild their total.

        Called after the new weight is stored. Override and call ``super()``
        to react to a weight change in the consumer's own code.
        """
        # Lazy because carrying.py imports this module — hoisting it to the
        # top is a circular import, not a tidy-up.
        from evennia_equipment.carrying import EquipmentCarryingMixin

        holder = self.location
        if isinstance(holder, EquipmentCarryingMixin):
            holder._recalculate_item_weight()
