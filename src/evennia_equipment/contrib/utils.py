# SPDX-License-Identifier: BSD-3-Clause
"""Helpers the contrib commands share.

Only contrib needs these: the library's own methods take a slot name or an enum
member, and never see what a player typed.
"""

from evennia_targeting import parse_match


def match_slot(wearer, text):
    """Turn what a player typed into a slot name this wearer has.

    The matching is ``evennia_targeting.parse_match(..., substring=True)``: an
    exact match wins outright — a game with both ``HAND`` and ``LEFT_HAND``
    needs that, or ``hand`` could never mean ``HAND`` — then the start of a
    word, then a substring. Case, spaces, underscores and hyphens are ignored,
    so how the consumer spelled the enum stops mattering.

    Matches this wearer's slots rather than the whole enum, so a humanoid
    asking for a dog neck is told it has none rather than told it is ambiguous.

    Args:
        wearer (Object): Whose slots to match against.
        text (str): What the player typed.

    Returns:
        tuple: ``(slot_name, None)`` with the real slot value, ready for
        ``wear()``, or ``(None, refusal)`` with a finished message.
    """
    # For the two refusals that leave a player with nothing to go on. The
    # ambiguous one does not get it — the options are already in the message.
    hint = "Type 'equipment' to see your wear slots."

    if not text.strip():
        # No verb: remove calls this too, so nothing here may assume wearing.
        return (None, f"Which slot? {hint}")

    hits = parse_match(text, list(wearer.worn_items or {}), substring=True)
    if not hits:
        return (None, f"You have no {text}. {hint}")
    if len(hits) == 1:
        return (hits[0], None)

    # Named rather than left to the player to guess a more specific word.
    # Items are not listed this way because a match could run to five; a wearer
    # has ten slots in total and a match rarely hits more than two.
    named = [name.replace("_", " ").lower() for name in hits]
    listed = f"{', '.join(named[:-1])} or {named[-1]}"
    return (None, f"Which do you mean — {listed}?")
