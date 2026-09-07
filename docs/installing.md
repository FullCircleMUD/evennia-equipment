# Installing

Everything a game does to get `evennia-equipment` running, in the order it does it. Work down the
list; the reasoning for each step is below it or in [design.md](design.md).

## 1. Install the package

Nothing is published yet, so install from a checkout:

```
pip install -e /path/to/evennia-equipment
```

## 2. Add the app

```python
# server/conf/settings.py
INSTALLED_APPS += ["evennia_equipment"]
```

This is what makes `AppConfig.ready()` run, which is what validates everything below. Leave it out
and nothing is checked — see *What is not checked for you*.

## 3. Declare your slots

One enum, naming every slot any creature in your game will ever have:

```python
# world/wearslots.py
from enum import Enum


class WearSlot(Enum):
    HEAD = "HEAD"
    BODY = "BODY"
    LEFT_HAND = "LEFT_HAND"
    RIGHT_HAND = "RIGHT_HAND"
    DOG_NECK = "DOG_NECK"
```

```python
# server/conf/settings.py
EQUIPMENT_WEARSLOTS = "world.wearslots.WearSlot"
```

This is the single list both sides are checked against — a creature's slots and an item's declaration
— which is what lets a typo in either be reported where it was written. Which creature gets which
slot is step 5.

## 4. Name your item identity

```python
EQUIPMENT_IDENTITY_ATTRIBUTE = "token_id"
```

The attribute an item carries as its permanent identity — a token id, an archive id, whatever your
game already uses. A database key will not do: a world rebuild reissues every one of them, which is
the situation this exists for. Only equipment recovery uses it; nothing else does.

## 5. Give your creatures a body plan

One small mixin per body plan, naming which slots that creature has:

```python
# typeclasses/equipment.py
from evennia_equipment.wearslots import EquipmentWearslotsMixin
from world.wearslots import WearSlot


class HumanoidEquipmentMixin(EquipmentWearslotsMixin):
    body_slots = (WearSlot.HEAD, WearSlot.BODY, WearSlot.LEFT_HAND, WearSlot.RIGHT_HAND)


class DogEquipmentMixin(EquipmentWearslotsMixin):
    body_slots = (WearSlot.DOG_NECK,)
```

Enum members, not strings — a typo is then an `AttributeError` on the line that wrote it. The
declaration is checked when the class is defined.

Then mix it into the typeclasses that wear things:

```python
class Character(HumanoidEquipmentMixin, DefaultCharacter):
    pass
```

## 6. Make your items carriable and wearable

```python
from evennia_equipment.carriable import EquipmentCarriableMixin, WeightProperty
from evennia_equipment.wearable import EquipmentWearableMixin, WearslotProperty


class Rock(EquipmentCarriableMixin, DefaultObject):
    weight = WeightProperty(2.0)


class Helmet(EquipmentWearableMixin, DefaultObject):
    weight = WeightProperty(1.5)
    wearslot = WearslotProperty([["HEAD"]])
```

An item's slots are a **list of groups**. Each group is one way of wearing it, and every slot in a
group is taken together:

```python
wearslot = WearslotProperty([["LEFT_HAND"], ["RIGHT_HAND"]])   # a ring, either hand
wearslot = WearslotProperty([["LEFT_HAND", "RIGHT_HAND"]])     # a greatsword, both
```

Re-declare `weight` and `wearslot` as their own property types, not as plain class attributes — a
plain attribute shadows the descriptor and loses both validation and persistence.

## 7. Containers, if you have them

```python
from evennia_equipment.container import EquipmentContainerMixin


class Backpack(EquipmentContainerMixin, DefaultObject):
    weight = WeightProperty(0.5)
```

A container has its own weight and adds its contents to whoever carries it. One whose contents should
*not* count — panniers on a mount — overrides `effective_weight` to return `self.weight` alone.

## 8. Wire up equipment recovery, if you archive

If your game rebuilds its world and restores characters, call
`update_worn_equipment_record()` on the character immediately before archiving it. Overriding your own
archive path and calling it there gives you one call site rather than scattered ones.

The library cannot do this for you: it has no way to know when you archive, and nothing it could hook
without learning that archiving exists.

## Required settings

| Setting | What it does | Without it |
|---|---|---|
| `EQUIPMENT_WEARSLOTS` | Module path to an `Enum` naming every slot in the game | The server does not start |
| `EQUIPMENT_IDENTITY_ATTRIBUTE` | The attribute an item carries as its permanent identity | The server does not start |

Both are refused at boot, and every problem across both is reported in one message so a consumer fixes
the whole list before restarting rather than once per mistake.

## Optional settings

This library reads no optional settings. Everything a game can vary is a class attribute or an
overridable method, because those are per creature or per item rather than per game.

## What is not checked for you

- **`INSTALLED_APPS`.** Leave the library out and `AppConfig.ready()` never runs, so nothing below is
  validated and the first sign of trouble is a wearer with no slots.
- **That your items actually carry `EQUIPMENT_IDENTITY_ATTRIBUTE`.** Nothing at boot can see an item.
  A name pointing at nothing yields `None` for every identity, and the symptom is an empty equipment
  record — everything else works.
- **That a typeclass carrying a wearslots mixin is one you meant to.** The declaration is checked when
  the class is defined; whether that class should have equipment at all is yours.
- **Anything written through `.db`.** `obj.db.weight = -5` bypasses validation entirely, because
  Evennia's attribute handler never reaches the descriptor. Assign to the property instead.
- **Which slot an item comes back in after a restore.** Recovery re-wears from the record, so a ring
  may return to the other hand. Preserving the exact slot would mean recording it, and the record is
  deliberately just identities.
