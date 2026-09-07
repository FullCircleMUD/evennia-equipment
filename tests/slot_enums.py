# SPDX-License-Identifier: BSD-3-Clause
"""Slot enums for the suite, standing in for a consumer's own module.

Imports nothing but ``enum`` — ``check_settings()`` resolves the path named in
the settings during ``django.setup()``, while the app registry is still being
built, so anything else this module imported would be pulled in at the worst
possible moment.

``WearSlot`` is what the suite boots with. The rest are the ways a consumer can
get the declaration wrong.
"""

from enum import Enum


class WearSlot(Enum):
    """Every slot any creature in this suite has."""

    HEAD = "HEAD"
    BODY = "BODY"
    LEFT_HAND = "LEFT_HAND"
    RIGHT_HAND = "RIGHT_HAND"
    DOG_NECK = "DOG_NECK"
    DOG_BODY = "DOG_BODY"


class NoMembers(Enum):
    """An enum declaring nothing. Legal Python, useless as a slot list."""


class NonStringValue(Enum):
    """A member whose value is not a string, so it cannot key a slot dict."""

    HEAD = "HEAD"
    BODY = 7


class RepeatedValue(Enum):
    """Two names, one value. Python folds the second into an alias, so this
    reads as three slots and is two."""

    HEAD = "HEAD"
    BODY = "BODY"
    SKULL = "HEAD"


#: Not an enum at all — what a consumer gets by pointing the setting at the
#: wrong name in the right module.
NOT_AN_ENUM = ["HEAD", "BODY"]
