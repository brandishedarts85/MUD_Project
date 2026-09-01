"""
Realms of Cyrisea - Equipment Commands
Expanded equipment system:
- Full RPG slot layout
- Bonus application
- Durability checks
- Wear/remove commands
- Equipment display
"""

import logging

# Expanded Cyrisea slot list
SLOTS = [
    "head",
    "face",
    "neck",
    "shoulders",
    "chest",
    "waist",
    "legs",
    "feet",
    "wrists",
    "hands",
    "ring1",
    "ring2",
    "weapon",
    "offhand",
    "ranged",
    "back",
]


async def do_wear(player, args):
    """Equip an item from inventory."""

    if not args:
        await player.send("Wear what.")
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

    # Determine slot
    slot = determine_slot(item)
    if not slot:
        await player.send("You can't wear that.")
        return

    # Check if slot is free
    if slot in player.equipment:
        await player.send(f"You are already wearing something on your {slot}.")
        return

    # Equip item
    player.equipment[slot] = item
    item.owner = player

    # Apply bonuses
    item.apply_bonuses(player)

    await player.send(f"You wear {item.colored_name()} on your {slot}.")

    # Durability warning
    if item.durability < item.max_durability * 0.2:
        await player.send("It looks worn and fragile.")


async def do_remove(player, args):
    """Remove an equipped item."""

    if not args:
        await player.send("Remove what.")
        return

    # Find equipped item
    slot = None
    item = None

    for s, obj in player.equipment.items():
        if obj.name.lower().startswith(args.lower()):
            slot = s
            item = obj
            break

    if not item:
        await player.send("You aren't wearing that.")
        return

    # Remove bonuses
    item.remove_bonuses(player)

    # Unequip
    del player.equipment[slot]
    item.owner = None

    await player.send(f"You remove {item.colored_name()} from your {slot}.")


async def do_equipment(player, args):
    """Show equipped items."""

    await player.send("\033[94mYour Equipment:\033[0m")

    if not player.equipment:
        await player.send("You are not wearing anything.")
        return

    for slot in SLOTS:
        item = player.equipment.get(slot)
        if item:
            await player.send(f"{slot.capitalize():10} : {item.colored_name()}")
        else:
            await player.send(f"{slot.capitalize():10} : (empty)")


# ---------------------------------------------------------
# Slot determination logic
# ---------------------------------------------------------

def determine_slot(item):
    """Determine which slot an item should occupy."""

    t = item.type

    if t == "weapon":
        return "weapon"
    if t == "shield":
        return "offhand"
    if t == "ranged":
        return "ranged"
    if t == "armor_head":
        return "head"
    if t == "armor_face":
        return "face"
    if t == "armor_neck":
        return "neck"
    if t == "armor_shoulders":
        return "shoulders"
    if t == "armor_chest":
        return "chest"
    if t == "armor_waist":
        return "waist"
    if t == "armor_legs":
        return "legs"
    if t == "armor_feet":
        return "feet"
    if t == "armor_wrists":
        return "wrists"
    if t == "armor_hands":
        return "hands"
    if t == "ring":
        # Choose first free ring slot
        return "ring1" if "ring1" not in player.equipment else "ring2"
    if t == "cloak":
        return "back"

    return None


# Command definitions
COMMAND_DEFS = [
    ("wear",      do_wear,      {"position": "standing", "help_category": "equipment"}),
    ("remove",    do_remove,    {"position": "standing", "help_category": "equipment"}),
    ("equipment", do_equipment, {"position": "standing", "help_category": "equipment"}),
]
