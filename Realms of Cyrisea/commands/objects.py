"""
Realms of Cyrisea - Object Interaction Commands
Enhanced object system:
- Weight & encumbrance
- Stackable items
- Containers
- Object tags (flammable, fragile, magical, heavy)
- get/drop/give/use
"""

import logging


# ---------------------------------------------------------
# Encumbrance system
# ---------------------------------------------------------

def inventory_weight(player):
    """Calculate total weight of player's inventory."""
    return sum(getattr(obj, "weight", 1) for obj in player.inventory)


def can_carry(player, obj):
    """Check if player can carry an object based on encumbrance."""
    max_weight = player.stamina * 5  # stamina determines carrying capacity
    return inventory_weight(player) + getattr(obj, "weight", 1) <= max_weight


# ---------------------------------------------------------
# GET
# ---------------------------------------------------------

async def do_get(player, args):
    """Pick up an item from the room."""

    if not args:
        await player.send("Get what.")
        return

    room = player.room

    # Find object
    obj = room.find_object(args)
    if not obj:
        await player.send("You don't see that here.")
        return

    # Weight check
    if not can_carry(player, obj):
        await player.send("It's too heavy for you to carry.")
        return

    # Stackable items
    if getattr(obj, "stackable", False):
        # Check if player already has a stack
        for inv_obj in player.inventory:
            if inv_obj.vnum == obj.vnum:
                inv_obj.quantity += getattr(obj, "quantity", 1)
                room.items.remove(obj)
                await player.send(f"You pick up {obj.short_desc}.")
                return

    # Normal item pickup
    room.items.remove(obj)
    player.inventory.append(obj)
    await player.send(f"You pick up {obj.short_desc}.")

    # Fragile items warning
    if "fragile" in getattr(obj, "tags", []):
        await player.send("You handle it carefully; it looks fragile.")


# ---------------------------------------------------------
# DROP
# ---------------------------------------------------------

async def do_drop(player, args):
    """Drop an item into the room."""

    if not args:
        await player.send("Drop what.")
        return

    # Find item
    item = None
    for obj in player.inventory:
        if obj.name.lower().startswith(args.lower()):
            item = obj
            break

    if not item:
        await player.send("You aren't carrying that.")
        return

    # Stackable items
    if getattr(item, "stackable", False) and getattr(item, "quantity", 1) > 1:
        item.quantity -= 1
        dropped = Object(
            vnum=item.vnum,
            name=item.name,
            short_desc=item.short_desc,
            long_desc=item.long_desc,
            type=item.type,
            value=item.value,
            rarity=item.rarity,
            durability=item.durability,
            max_durability=item.max_durability,
            bonuses=item.bonuses,
            consumable=item.consumable,
            use_effect=item.use_effect,
            material=item.material,
        )
        dropped.quantity = 1
        player.room.items.append(dropped)
        await player.send(f"You drop one {item.short_desc}.")
        return

    # Normal drop
    player.inventory.remove(item)
    player.room.items.append(item)
    await player.send(f"You drop {item.short_desc}.")

    # Fragile items may break
    if "fragile" in getattr(item, "tags", []):
        if random.randint(1, 100) <= 25:
            await player.send(f"{item.short_desc} shatters on the ground!")
            player.room.items.remove(item)


# ---------------------------------------------------------
# GIVE
# ---------------------------------------------------------

async def do_give(player, args):
    """Give an item to another player."""

    parts = args.split(maxsplit=1)
    if len(parts) < 2:
        await player.send("Give what to whom.")
        return

    item_name, target_name = parts
    target = player.room.find_player(target_name)

    if not target:
        await player.send("They aren't here.")
        return

    # Find item
    item = None
    for obj in player.inventory:
        if obj.name.lower().startswith(item_name.lower()):
            item = obj
            break

    if not item:
        await player.send("You aren't carrying that.")
        return

    # Weight check for target
    if not can_carry(target, item):
        await player.send("They can't carry that.")
        return

    # Transfer item
    player.inventory.remove(item)
    target.inventory.append(item)

    await player.send(f"You give {item.short_desc} to {target.name}.")
    await target.send(f"{player.name} gives you {item.short_desc}.")


# ---------------------------------------------------------
# USE
# ---------------------------------------------------------

async def do_use(player, args):
    """Use a consumable item."""

    if not args:
        await player.send("Use what.")
        return

    # Find item
    item = None
    for obj in player.inventory:
        if obj.name.lower().startswith(args.lower()):
            item = obj
            break

    if not item:
        await player.send("You aren't carrying that.")
        return

    await item.use(player)


# ---------------------------------------------------------
# Command definitions
# ---------------------------------------------------------

COMMAND_DEFS = [
    ("get",   do_get,   {"position": "standing", "help_category": "objects"}),
    ("drop",  do_drop,  {"position": "standing", "help_category": "objects"}),
    ("give",  do_give,  {"position": "standing", "help_category": "objects"}),
    ("use",   do_use,   {"position": "standing", "help_category": "objects"}),
]
