# SPDX-License-Identifier: BSD-3-Clause
"""Helpers the contrib commands share.

Only contrib needs these: the library's own methods take a slot name or an enum
member, and never see what a player typed.
"""


def normalise_slot(text):
    """Reduce a string to the form slot names are compared in.

    Upper case, with spaces, underscores and hyphens removed. **Both sides go
    through it**, which is the point — it stops mattering how a consumer spelled
    the enum, so a game with ``RIGHT_FINGER`` and a game with ``RIGHTFINGER``
    both answer to every spelling of it a player might type.

    The result is for comparison only. What reaches ``wear()`` is the real slot
    value, looked up once the match is made.

    Args:
        text (str): What the player typed, or a slot name.

    Returns:
        str: The canonical form. Empty in, empty out — ``wear ring on `` gets
        here, and a raise would be a traceback where a refusal belongs.
    """
    # Every separator a slot name might be written with, so a mixture of them
    # is no different to one.
    return text.strip().upper().replace(" ", "").replace("_", "").replace("-", "")


def match_slot(wearer, text):
    """Turn what a player typed into a slot name this wearer has.

    An exact match on the normalised form wins outright — a game with both
    ``HAND`` and ``LEFT_HAND`` needs that, or ``hand`` could never mean
    ``HAND``. Failing that, a substring match, which is one answer or a
    question.

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

    wanted = normalise_slot(text)
    if not wanted:
        # No verb: remove calls this too, so nothing here may assume wearing.
        return (None, f"Which slot? {hint}")

    # Normalised form to the real one, which is what wear() has to be given.
    slots = {normalise_slot(name): name for name in (wearer.worn_items or {})}

    if wanted in slots:
        return (slots[wanted], None)

    hits = [real for form, real in slots.items() if wanted in form]
    if not hits:
        return (None, f"You have no {text}. {hint}")
    if len(hits) == 1:
        return (hits[0], None)

    # Named rather than left to the player to guess a more specific word.
    # Items are not listed this way because a match could run to five; a wearer
    # has ten slots in total and a substring rarely hits more than two.
    named = [name.replace("_", " ").lower() for name in hits]
    listed = f"{', '.join(named[:-1])} or {named[-1]}"
    return (None, f"Which do you mean — {listed}?")
