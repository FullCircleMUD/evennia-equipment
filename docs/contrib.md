# The contrib commands

Four optional commands — `wear`, `remove`, `equipment`, `inventory` — each as a mixin to compose onto a
game's own command class, and as a concrete command ready to use. Nothing in the library imports them.

## 1. Compose them onto your commands

A game with its own command base — gates, prompts, a combat queue — composes the mixins onto it:

```python
from evennia_equipment.contrib import (
    CmdEquipmentMixin,
    CmdInventoryMixin,
    CmdRemoveMixin,
    CmdWearMixin,
)

from commands.command import Command   # your game's base


class CmdWear(CmdWearMixin, Command):
    """Put something on. Usage: wear <item> [on <slot>]"""

    key = "wear"
```

The mixin carries the behaviour; your class carries the key, aliases, locks and help text. Evennia reads
help from the class's own docstring, so write one on yours.

## 2. Or install the command set

For a game without its own base, `EquipmentCmdSet` holds the four concrete commands:

```python
# commands/default_cmdsets.py
from evennia import default_cmds
from evennia_equipment.contrib import EquipmentCmdSet


class CharacterCmdSet(default_cmds.CharacterCmdSet):
    def at_cmdset_creation(self):
        super().at_cmdset_creation()
        self.add(EquipmentCmdSet)
```

**Added after the defaults.** Merging is by key and the later set wins, so `inventory` replaces
Evennia's. The other three keys are new.

## 3. What each one does

### wear

```
wear <item>
wear <item> on <slot>
```

Finds the item among what the caller carries, checks it has somewhere to go, and puts it on. Naming a
slot overrides the item's default — a ring on the finger asked for, a sword held rather than wielded.

### remove

```
remove <item>
remove <item> from <slot>
remove from <slot>
```

Takes something off, leaving it carried. With two identical rings, one on each hand, `remove ring` takes
the first and `remove from right hand` is how to say which.

### equipment

```
equipment
eq
```

Every slot the caller has, in body-plan order, with what is in it:

```
Equipped Items

  <Head>        an iron helmet
  <Body>
  <Left Hand>   a greatsword
  <Right Hand>  a greatsword
```

### inventory

```
inventory
inv
i
```

What is carried and **not** worn, then what it weighs:

```
Inventory:

  a healing potion (3)
  a longsword
  a longsword

Carrying 9.5 of 40.0.
```

Items stack when they say they do: `stackable` is `True` by default; set it `False` on anything a player
would not treat as interchangeable.

## 4. The seams

| Seam | On | Override it to |
|---|---|---|
| `announce(item)` | `wear`, `remove` | tell the room through your game's messaging. The default is `msg_contents` |
| `at_success(item)` | `wear`, `remove` | do anything that follows success — a time wait in a fight. The default does nothing |
| `extra_lines()` | `inventory` | add lines between the items and the summary — balances, resources |
| `slot_column_gap` | `equipment` | widen the space after the slot column |
| `slot`, `verb` | `wear` | make `wield` or `hold` of it: `slot` fixes where the item goes, `verb` words the lines |

`announce` and `at_success` run only when the item went on or came off.

```python
class CmdInventory(CmdInventoryMixin, Command):
    key = "inventory"

    def extra_lines(self):
        return [f"  {self.caller.gold} gold"]
```

## 5. The helpers underneath

`wear` and `remove` are built on helpers any command can use:

- **`evennia_equipment.finders.find_carried(caller, text)`** and **`find_worn(caller, text)`** — the
  item a player names, through Evennia's own search, so aliases and `sword-2` work.
- **`evennia_equipment.finders.match_slot(caller, text)`** — typed text as one of the caller's slots.
- **`evennia_equipment.contrib.utils.resolve_wear(caller, text)`** and **`resolve_remove(caller,
  text)`** — the whole `wear` and `remove` argument.

Each returns `(answer, None)` or `(None, refusal)`, and sends nothing. An `enchant` command finding
something in the player's pack calls `find_carried(caller, self.args)` and has its item or its refusal.

Slot names match ignoring case, spaces, underscores and hyphens: `wear ring on right finger` and
`remove from right_finger` both work. **Do not put the spaced word ` on ` or ` from ` in a wearable's
name** — the argument splits on it. *An onyx ring* and *a bone helm* are fine.

## 6. What is not here

**`get`, `drop` and `give` are Evennia's.** `CmdGet` calls `obj.move_to(caller)`, so the carrying
refusal fires with no command of ours.

**`wield` and `hold` are your game's**, because the slot names are. Each is `CmdWearMixin` with `slot`
and `verb` set:

```python
class CmdWield(CmdWearMixin, Command):
    key = "wield"
    slot = WearSlot.WIELD
    verb = "wield"
```

## Learn more

- **[design.md](design.md)** — why the commands and the methods under them are shaped this way.
- **[installing.md](installing.md)** — getting the library itself running.
- **[test-plan.md](test-plan.md)** — the `FC`, `FW`, `MS`, `UW`, `UR`, `CW`, `CM`, `CE`, `CI` and `CS`
  cases.
