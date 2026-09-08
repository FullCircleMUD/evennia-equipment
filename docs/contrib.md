# The contrib commands

Four optional commands, so a game gets a working vocabulary without writing one. Nothing in the library
imports them, and a game driving the mixins from its own code never installs them.

**They are meant to be read and replaced.** Almost every game will replace `inventory` — the
interesting parts of a listing are the parts only that game knows about. That is the bargain: a worked
example rather than shared infrastructure.

## 1. Install the command set

One line in the cmdset your game already has:

```python
# commands/default_cmdsets.py
from evennia import default_cmds
from evennia_equipment.contrib import EquipmentCmdSet


class CharacterCmdSet(default_cmds.CharacterCmdSet):
    def at_cmdset_creation(self):
        super().at_cmdset_creation()
        self.add(EquipmentCmdSet)
```

**Added after the defaults, on purpose.** Merging is by key, and the later set wins — so `inventory`
replaces Evennia's rather than competing with it, and nothing has to be removed first. The other three
keys are new, so they simply appear.

Taking some of them is ordinary Evennia:

```python
self.add(CmdWear())          # three of the four
self.add(MyOwnInventory())   # ours, then yours on top
```

## 2. What each one does

### wear

```
wear <item>
wear <item> on <slot>
```

Puts something on. Without a slot the item's own preference decides — a ring goes on the first free
finger. Naming one overrides that, which is how a player wears a ring on the hand they meant, or holds
a sword that would otherwise be wielded.

The refusals come from the mixin, so they read the same however a player reached them: *you are not
carrying that*, *you are already wearing it*, *you have nowhere to wear it*.

### remove

```
remove <item>
remove <item> from <slot>
remove from <slot>
```

Takes something off, leaving it carried. Taking something off does not put it down.

The third form has no counterpart in `wear`, and it is the reason slots can be named at all: with two
identical rings, one on each hand, `remove ring` takes whichever came first and `remove from right
hand` is the only way to say which.

### equipment

```
equipment
eq
```

Every slot the character has, in the order its body plan declares them:

```
Equipped Items

  <Head>        an iron helmet
  <Body>
  <Left Hand>   a greatsword
  <Right Hand>  a greatsword
```

An empty slot shows its name and nothing else — the absence is the information. A two-handed item
appears under both slots it fills, because it occupies both and showing it once would leave a hand
looking free.

The column width is computed from the longest slot name, so an unusual body plan still aligns.
`slot_column_gap` sets the space after it.

### inventory

```
inventory
inv
i
```

What is held and **not** worn, which is the reason this replaces Evennia's — that one lists everything
in `contents` and so offers a player the armour they are wearing.

```
Inventory:

  a healing potion (3)
  a longsword
  a longsword

Carrying 9.5 of 40.0.
```

Items stack when they say they do. `stackable` is `True` by default; set it `False` on anything a
player would not treat as interchangeable, and each gets its own line. Two longswords are not the same
longsword once one is chipped, and only your game knows that.

The summary names a limit only when one is set, since capacity is unlimited by default.

## 3. Naming a slot

`wear ring on right finger` and `remove from right_finger` both work, and so does `rightfinger`. Both
the typed text and your slot names are reduced to one form before comparison — upper case, with spaces,
underscores and hyphens removed — so it stops mattering how you spelled the enum.

An exact match wins; failing that, a substring. `hand` on a humanoid asks which:

```
Which do you mean — left hand or right hand?
```

Matching is against **that character's** slots, not every slot in your game, so a humanoid asking for a
dog neck is told it has none.

One consequence worth knowing: the split is on the word ` on ` or ` from ` with spaces either side, so
**do not put either in a wearable's name.** The letters are fine — *an onyx ring* and *a bone helm* are
safe.

## 4. Adding your own lines to the inventory

`extra_lines()` is the one seam these commands provide. It returns `[]`, and yours returns whatever
your game carries that is not an object — currency, resources, charges:

```python
class MyInventory(CmdInventory):
    def extra_lines(self):
        return [f"  {self.caller.gold} gold"]
```

They appear between the items and the carrying summary, because a balance is something you are carrying
and belongs above the line that totals what you carry.

**There are no other seams.** Anything else you want different, you get by overriding `func()` — which
is what replacing a contrib module means, and what a game with condition labels, visibility rules or
its own layout will do.

## 5. What is not here

**`get`, `drop` and `give` are Evennia's**, untouched. `CmdGet` calls `obj.move_to(caller)`, so
`at_pre_object_receive` already fires and a refusal from the carrying mixin is respected without a
command of ours.

**`wield` and `hold` are your game's.** They only mean something where an item's natural slot differs
from where a player sometimes wants it, and the slot names come from your enum. `wear sword on wield`
does everything `wield sword` does, so the capability is already here — the shorthand verb is two short
subclasses in your own code.

**Nothing renders your game's concepts.** Condition, enchantment, ownership, what a blind character can
make out — all absent, and all reasons to replace a command rather than configure it. Item names go
through Evennia's own `get_display_name(looker)`, so a game that overrides that gets it here for free.

## Learn more

- **[design.md](design.md)** — the mixin family these commands sit on, and the reasoning behind them.
- **[installing.md](installing.md)** — getting the library itself running.
- **[test-plan.md](test-plan.md)** — the `CW`, `CM`, `CE`, `CI`, `CS`, `NS` and `SM` cases cover this.
