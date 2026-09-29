# SPDX-License-Identifier: BSD-3-Clause
"""Turning what a player typed after ``wear`` or ``remove`` into what the
methods take.

Built on the core finders: ``find_carried()``, ``find_worn()`` and
``match_slot()`` do the looking, and these add the ``on`` and ``from`` of the
two commands. Each returns ``(answer, None)`` or ``(None, refusal)`` with a
finished message, and messages no one.
"""

from evennia_targeting import f_key_matches, parse_split

from evennia_equipment.finders import find_carried, find_worn, match_slot


def resolve_wear(caller, text):
    """Turn ``<item>`` or ``<item> on <slot>`` into the item and the slot.

    The slot is matched first, so a mistyped slot never reaches the item
    lookup. Either refusal is returned unchanged. See UW-03 and UW-04.

    Args:
        caller (Object): Who is wearing.
        text (str): What the player typed after the command.

    Returns:
        tuple: ``((item, slot), None)`` — ``slot`` an enum member, or ``None``
        when none was named — or ``(None, refusal)``.
    """
    item_text, slot_text = parse_split(text, "on")

    slot = None
    if slot_text is not None:
        slot, refusal = match_slot(caller, slot_text)
        if refusal:
            return (None, refusal)

    item, refusal = find_carried(caller, item_text)
    if refusal:
        return (None, refusal)
    return ((item, slot), None)


def resolve_remove(caller, text):
    """Turn ``<item>``, ``<item> from <slot>`` or ``from <slot>`` into the item.

    With a slot, the item is whatever is in it, and a name given as well has to
    match that item — which is how a player says which of two rings sharing a
    key. See UR-03.

    Args:
        caller (Object): Who is removing.
        text (str): What the player typed after the command.

    Returns:
        tuple: ``(item, None)``, or ``(None, refusal)``.
    """
    item_text, slot_text = parse_split(text, "from")
    if slot_text is None:
        return find_worn(caller, item_text)

    slot, refusal = match_slot(caller, slot_text)
    if refusal:
        return (None, refusal)

    named = slot.value.replace("_", " ").lower()
    in_slot = caller.worn_items[slot.value]
    if in_slot is None:
        return (None, f"You are wearing nothing on your {named}.")
    if item_text and not f_key_matches(item_text)(in_slot, caller):
        return (None, f"You are not wearing {item_text} on your {named}.")
    return (in_slot, None)
