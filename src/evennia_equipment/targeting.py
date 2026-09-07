# SPDX-License-Identifier: BSD-3-Clause
"""The filters this library publishes for ``evennia-targeting``.

Every walk this library makes over an object's ``contents`` is built from these,
and they are exported so a consumer filtering by the same thing uses this
definition rather than writing a second one that has to be fixed separately.

The module is named ``targeting.py`` because every library extending
``evennia-targeting`` names it that — ``find . -name targeting.py`` is how one
codebase sees what another has already written.

Both are factories rather than predicates: each closes over data assembled once,
rather than recomputing it for every object a walk visits.
"""


def f_worn_by(wearer):
    """Build a predicate matching the items ``wearer`` currently has on.

    Identity, not equality. A set membership test uses ``__hash__`` and
    ``__eq__``, either of which a consumer's typeclass may define by key or by
    token id — two rings that compare equal would then both read as worn.

    The slots are read once, here, so the predicate is a snapshot of the moment
    it was built rather than a live view. That is what a walk wants: one read
    for the whole pass, not one per object.

    Args:
        wearer: The object whose slots decide the answer.

    Returns:
        callable: An ``(obj, caller) -> bool`` predicate.
    """
    occupied = wearer._occupied_ids()

    def _worn_by(obj, caller):
        return id(obj) in occupied

    return _worn_by


def f_identity_in(identities):
    """Build a predicate matching items whose ``wearslot_identity`` is in a set.

    ``getattr`` with a default, not a plain read: a character carries rocks and
    bread as well as armour, and a plain carriable item has no
    ``wearslot_identity`` to ask about.

    An empty set matches nothing rather than raising, which is where this
    differs from ``evennia-targeting``'s own factories. There, empty arguments
    can only be a caller bug; here an empty record is the ordinary state of
    someone who was wearing nothing, and ``restore_worn()`` reaches it normally.

    Args:
        identities: The identities to match against. Empty matches nothing.

    Returns:
        callable: An ``(obj, caller) -> bool`` predicate.
    """
    # Copied, so the predicate is a snapshot like f_worn_by's, and so a stored
    # attribute is not re-read once per object the walk visits.
    identities = frozenset(identities)

    def _identity_in(obj, caller):
        return getattr(obj, "wearslot_identity", None) in identities

    return _identity_in
