# SPDX-License-Identifier: BSD-3-Clause
"""The setting this library reads, and the boot check that refuses a bad one.

The slot names a game uses reach the library as a setting naming an enum — see
``library-standards.md`` § Consumer-authored config, and the same shape as
``evennia-survival``'s stages. There is no slot list the library could invent,
so the setting has no safe default: it is validated once at boot and the
instance does not start without it::

    EQUIPMENT_WEARSLOTS = "world.wearslots.WearSlot"

    class WearSlot(Enum):
        HEAD = "HEAD"
        BODY = "BODY"
        LEFT_HAND = "LEFT_HAND"

**One enum for every slot the game will ever have.** Which of them a given
creature gets is a wearslots subclass's business. This is the single list both
sides are checked against — a wearer's slots and an item's declaration — which
is what makes a typo in either one reportable.

No base class for the enum. A slot carries one thing, its name; survival needs
a base because a stage carries three.

The checks are sequential rather than collected: each one makes the next
meaningful, so only one can be wrong at a time.
"""

from enum import Enum
from functools import lru_cache

from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string

SETTING_WEARSLOTS = "EQUIPMENT_WEARSLOTS"

_EXAMPLE = "'world.wearslots.WearSlot'"


def check_settings() -> None:
    """Refuse to start when the declared slot enum is missing or unusable.

    Called from ``AppConfig.ready()``.
    """
    from django.conf import settings

    path = getattr(settings, SETTING_WEARSLOTS, None)
    if not path:
        raise ImproperlyConfigured(
            f"{SETTING_WEARSLOTS} is not set. Point it at an Enum naming every "
            f"slot your game uses, e.g. {_EXAMPLE}."
        )

    try:
        # import_string rather than variable_from_module: the latter returns
        # None for a missing module, a missing name and a real None alike, so
        # a typo would arrive indistinguishable from a deliberate absence.
        slots = import_string(path)
    except Exception as exc:
        # The module exists because this library asked for it, so its state is
        # our business to report. Chained rather than swallowed, so a consumer
        # gets both the setting that is wrong and why.
        raise ImproperlyConfigured(
            f"{SETTING_WEARSLOTS} names {path!r}, which could not be loaded."
        ) from exc

    if not (isinstance(slots, type) and issubclass(slots, Enum)):
        raise ImproperlyConfigured(
            f"{SETTING_WEARSLOTS} names {path!r}, which is "
            f"{type(slots).__name__} and not an Enum. Declare your slots as an "
            f"Enum, one member per slot."
        )

    if not list(slots):
        raise ImproperlyConfigured(
            f"{SETTING_WEARSLOTS} names {path!r}, which declares no members. "
            f"A game with no slots does not need this library."
        )

    # Read __members__, not the members, and read it first. Python folds a
    # repeated value into the member declared before it, so by the time the
    # members are examined the duplicate is gone and what remains looks
    # perfectly well formed.
    aliases = [name for name, member in slots.__members__.items() if name != member.name]
    if aliases:
        raise ImproperlyConfigured(
            f"{SETTING_WEARSLOTS} names {path!r}, where {', '.join(aliases)} "
            f"repeat a value already in use. Python folds each one into the "
            f"member declared before it, leaving the game short a slot."
        )

    not_strings = sorted(
        member.name for member in slots if not isinstance(member.value, str)
    )
    if not_strings:
        raise ImproperlyConfigured(
            f"{SETTING_WEARSLOTS} names {path!r}, where {', '.join(not_strings)} "
            f"have values that are not strings. A slot name keys a dictionary "
            f"and is matched against an item's declaration, so it must be text."
        )


@lru_cache(maxsize=1)
def valid_slot_names() -> frozenset:
    """Return every slot name the consumer declared. Checked at boot.

    Resolved once and held for the life of the process. The enum comes from a
    setting naming a module, and neither settings nor an imported module can
    change while the server is up — a reload restarts the process, which is
    where a changed enum takes effect. So there is nothing to invalidate, and
    a consumer never needs to clear it.

    A test that swaps the setting does need to: call
    ``valid_slot_names.cache_clear()``.
    """
    from django.conf import settings

    return frozenset(
        member.value for member in import_string(getattr(settings, SETTING_WEARSLOTS))
    )
