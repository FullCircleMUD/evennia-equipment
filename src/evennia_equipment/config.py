# SPDX-License-Identifier: BSD-3-Clause
"""The setting this library reads, and the boot check that refuses a bad one.

Slot layouts reach the library as a setting naming a module — see
``library-standards.md`` § Consumer-authored config. There is no layout the
library could invent, so the setting has no safe default: it is validated once
at boot and the instance does not start without it.

One setting rather than one per creature type. A game has as many layouts as it
has body plans, and they are collected in the consumer's own module rather than
in ``settings.py``::

    EQUIPMENT_WEARSLOTS = "world.wearslots.LAYOUTS"

    LAYOUTS = {
        "humanoid": ["HEAD", "FACE", "NECK", ...],
        "dog": ["DOG_NECK", "DOG_BODY"],
    }

Every problem is collected and raised together. A consumer installing this has
more than one thing to get right, and stopping at the first turns that into
fix-restart-fix-restart, once per mistake.
"""

from functools import lru_cache

from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string

SETTING_WEARSLOTS = "EQUIPMENT_WEARSLOTS"

#: What each collected problem is prefixed with in the refusal message. One
#: problem per line, so a consumer with three things wrong works through a list
#: rather than a paragraph. Named so a test can count problems without pinning
#: any wording.
PROBLEM_PREFIX = "\n  - "

_EXAMPLE = "'world.wearslots.LAYOUTS'"


def check_settings() -> None:
    """Refuse to start when the declared layouts are missing or unusable.

    Called from ``AppConfig.ready()``. Collects every problem and raises once,
    so a consumer gets the whole list.
    """
    from django.conf import settings

    problems = []
    cause = None
    layouts = None

    path = getattr(settings, SETTING_WEARSLOTS, None)
    if not path:
        problems.append(
            f"{SETTING_WEARSLOTS} is not set. Point it at a mapping of layout "
            f"name to slot names, e.g. {_EXAMPLE}."
        )
    else:
        try:
            # import_string rather than variable_from_module: the latter
            # returns None for a missing module, a missing name, and a real
            # None alike, so a typo would arrive here indistinguishable from
            # a layout set deliberately empty.
            layouts = import_string(path)
        except Exception as exc:
            # The module exists because this library asked for it, so its
            # state is our business to report. Chained rather than swallowed,
            # so the consumer gets the setting that is wrong and why.
            cause = exc
            problems.append(
                f"{SETTING_WEARSLOTS} names {path!r}, which could not be loaded."
            )

    if layouts is not None:
        if not isinstance(layouts, dict):
            problems.append(
                f"{SETTING_WEARSLOTS} names {path!r}, which is {type(layouts).__name__} "
                f"and not a mapping. It must map a layout name to that layout's "
                f"slot names."
            )
        else:
            for name, slots in layouts.items():
                problems.extend(_problems_with(path, name, slots))

    if problems:
        raise ImproperlyConfigured(
            "evennia-equipment cannot start:"
            + "".join(f"{PROBLEM_PREFIX}{problem}" for problem in problems)
        ) from cause


@lru_cache(maxsize=1)
def get_wearslot_layouts():
    """Return the consumer's declared layouts. Checked at boot.

    Resolved once and held for the life of the process. The layouts come from
    a setting naming a module, and neither settings nor an imported module can
    change while the server is up — a reload restarts the process, which is
    where a changed layout takes effect. So there is nothing to invalidate,
    and a consumer never needs to clear it.

    A test that swaps the setting does need to: call
    ``get_wearslot_layouts.cache_clear()``.
    """
    from django.conf import settings

    return import_string(getattr(settings, SETTING_WEARSLOTS))


def known_slot_names() -> set:
    """Return every slot name across every declared layout.

    Derived rather than cached at boot: an item's slots are set at creation
    and not per tick, so the cost is a module lookup and a comprehension, and
    nothing has to invalidate anything when the layouts change.

    The union is as far as an item-side check can go. Which creature has which
    slot is `wear()`'s business, where both sides are present.
    """
    return {slot for layout in get_wearslot_layouts().values() for slot in layout}


def _problems_with(path: str, name: str, slots) -> list:
    """Return everything wrong with one declared layout.

    Each check that would be meaningless after the one before it returns
    early, so a consumer gets one problem per mistake rather than a cascade.
    """
    # Before anything else: a string satisfies every test below. It is
    # iterable, it has a length, and membership against it succeeds one
    # letter at a time — so "HEAD" would silently become four slots.
    if isinstance(slots, str):
        return [
            f"{SETTING_WEARSLOTS} names {path!r}, whose {name!r} layout is the "
            f"string {slots!r}. It must be a list of slot names; a bare string "
            f"is read one letter at a time."
        ]

    try:
        slots = list(slots)
    except TypeError:
        return [
            f"{SETTING_WEARSLOTS} names {path!r}, whose {name!r} layout is "
            f"{type(slots).__name__} and cannot be read as a list of slot names."
        ]

    if not slots:
        return [
            f"{SETTING_WEARSLOTS} names {path!r}, whose {name!r} layout declares "
            f"no slots. A creature that wears nothing does not carry the mixin, "
            f"so an empty layout is a typo rather than a choice."
        ]

    problems = []

    not_strings = [slot for slot in slots if not isinstance(slot, str)]
    if not_strings:
        problems.append(
            f"{SETTING_WEARSLOTS} names {path!r}, whose {name!r} layout holds "
            f"{not_strings!r}. Every slot name must be a string."
        )

    seen = set()
    repeated = sorted(
        {slot for slot in slots if isinstance(slot, str) and (slot in seen or seen.add(slot))}
    )
    if repeated:
        problems.append(
            f"{SETTING_WEARSLOTS} names {path!r}, whose {name!r} layout repeats "
            f"{', '.join(repeated)}. A repeated name is folded into one slot, "
            f"leaving the layout shorter than it reads."
        )

    return problems
