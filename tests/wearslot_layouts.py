# SPDX-License-Identifier: BSD-3-Clause
"""Slot layouts for the suite, standing in for a consumer's own module.

Imports nothing — ``check_settings()`` resolves the path named in the settings
during ``django.setup()``, while the app registry is still being built, so
anything this module imported would be pulled in at the worst moment.

Each name is what the good and bad cases point ``EQUIPMENT_WEARSLOTS`` at.
"""

LAYOUTS = {
    "humanoid": ["HEAD", "BODY", "LEFT_HAND", "RIGHT_HAND"],
    "dog": ["DOG_NECK", "DOG_BODY"],
}

EMPTY = {}

EMPTY_LAYOUT = {"humanoid": []}

NOT_A_MAPPING = ["HEAD", "BODY"]

BARE_STRING_LAYOUT = {"humanoid": "HEAD"}

NON_STRING_ENTRY = {"humanoid": ["HEAD", 7]}

REPEATED_NAME = {"humanoid": ["HEAD", "BODY", "HEAD"]}

SEVERAL_PROBLEMS = {"humanoid": "HEAD", "dog": ["DOG_NECK", 7]}

#: The humanoid layout with one slot added, for the case proving slots are read
#: from the layout rather than copied when a wearer is created.
LAYOUT_WITH_A_NEW_SLOT = {
    "humanoid": ["HEAD", "BODY", "LEFT_HAND", "RIGHT_HAND", "TAIL"],
    "dog": ["DOG_NECK", "DOG_BODY"],
}
