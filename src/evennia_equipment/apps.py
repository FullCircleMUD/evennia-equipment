# SPDX-License-Identifier: BSD-3-Clause
"""The Django app, and the one thing it does at boot.

``ready()`` validates the consumer's configuration and nothing else. Checking
here rather than at first use is the point: validation deferred to the first
``wear()`` means a misconfigured instance starts cleanly, runs, and then fails
in front of a player with a message about nothing in particular.
"""

from django.apps import AppConfig


class EquipmentConfig(AppConfig):
    """Refuses the boot when the declared wearslot layouts are unusable."""

    name = "evennia_equipment"
    label = "evennia_equipment"
    verbose_name = "Evennia Equipment"

    def ready(self):
        from evennia_equipment.config import check_settings

        check_settings()
