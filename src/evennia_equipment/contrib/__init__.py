# SPDX-License-Identifier: BSD-3-Clause
"""Optional commands, for a game that wants a working set rather than its own.

Nothing here is imported by the library itself, and a consumer driving the
mixins from their own code never installs it. What it provides is the vocabulary
Evennia has no word for — wearing, removing, and reading a slot sheet.

These are meant to be **read and replaced**, not configured. There are no
display hooks: a game wanting different output overrides the command, which is
what almost every game will do, since the interesting parts of an inventory
listing are the parts only that game knows about.
"""
