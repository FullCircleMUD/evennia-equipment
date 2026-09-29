# SPDX-License-Identifier: BSD-3-Clause
"""Finding what a player names among what they carry, what they wear, and
their slots.

For any command that acts on a player's inventory or equipment — wearing,
removing, enchanting, giving. Each returns ``(answer, None)`` or
``(None, refusal)`` with a finished message, and messages no one: the command
speaks.
"""

from evennia_targeting import op_not, parse_match, walk_contents

from evennia_equipment.config import get_slot_enum
from evennia_equipment.targeting import f_worn_by


def find_carried(caller, text):
    """Find the item ``text`` names among what ``caller`` carries and is not
    wearing.

    Args:
        caller (Object): Whose inventory to look in.
        text (str): What the player typed.

    Returns:
        tuple: ``(item, None)``, or ``(None, refusal)``. A name matching only
        something worn is refused naming it. See FC-07.
    """
    return _find(
        caller,
        text,
        here=op_not(f_worn_by(caller)),
        elsewhere=f_worn_by(caller),
        found_elsewhere="You are already wearing {item}.",
    )


def find_worn(caller, text):
    """Find the item ``text`` names among what ``caller`` is wearing.

    Args:
        caller (Object): Whose equipment to look in.
        text (str): What the player typed.

    Returns:
        tuple: ``(item, None)``, or ``(None, refusal)``. A name matching only
        something carried is refused naming it. See FW-06.
    """
    return _find(
        caller,
        text,
        here=f_worn_by(caller),
        elsewhere=op_not(f_worn_by(caller)),
        found_elsewhere="You are not wearing {item}.",
    )


def _find(caller, text, here, elsewhere, found_elsewhere):
    """Match ``text`` among the caller's items passing ``here``, then say why
    not — naming an item passing ``elsewhere`` if one matches instead.

    The matching is Evennia's own ``caller.search``, so aliases and ``sword-2``
    work as they do in every other command. See FC-03 and FC-06.
    """
    text = text.strip()
    if not text:
        return (None, "What do you mean?")

    matches = _search(caller, text, walk_contents(caller, caller, here))
    if matches:
        # Items sharing a key are interchangeable, so the first is the answer.
        # Differing keys are a real question, and the reply echoes what was
        # typed rather than listing candidates. See FC-04 and FC-05.
        if len({obj.key.lower() for obj in matches}) > 1:
            return (None, f"Which {text} do you mean?")
        return (matches[0], None)

    other = _search(caller, text, walk_contents(caller, caller, elsewhere))
    if other:
        return (None, found_elsewhere.format(item=other[0]))

    return (None, f"You are not carrying {text}.")


def _search(caller, text, candidates):
    """``caller.search`` over ``candidates`` only, silently.

    ``quiet=True`` so Evennia sends nothing itself (FC-10). ``use_dbref=False``
    because a ``#dbref`` makes the search global and ignores the candidates —
    a builder typing ``wear #12`` would otherwise reach anything in the game.
    """
    return caller.search(text, candidates=candidates, quiet=True, use_dbref=False)


def match_slot(caller, text):
    """Turn what a player typed into a member of the slot enum, from the
    slots ``caller`` has.

    The matching is ``evennia_targeting.parse_match(..., substring=True)`` over
    the caller's own slot names, so case, spaces, underscores and hyphens do
    not matter, and a slot this caller lacks matches nothing. See MS-01 and
    MS-04.

    Args:
        caller (Object): Whose slots to match against.
        text (str): What the player typed.

    Returns:
        tuple: ``(member, None)``, ready for ``wear()`` and ``slots_for()``, or
        ``(None, refusal)``.
    """
    hint = "Type 'equipment' to see your slots."

    if not text.strip():
        # An empty string matched as a substring would hit every slot. MS-05.
        return (None, f"Which slot? {hint}")

    hits = parse_match(text, list(caller.worn_items), substring=True)
    if not hits:
        return (None, f"You have no {text.strip()}. {hint}")
    if len(hits) > 1:
        named = [name.replace("_", " ").lower() for name in hits]
        listed = f"{', '.join(named[:-1])} or {named[-1]}"
        return (None, f"Which do you mean — {listed}?")
    return (get_slot_enum()(hits[0]), None)
