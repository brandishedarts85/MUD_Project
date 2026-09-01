"""
Realms of Cyrisea - Information Commands
Enhanced look/examine system:
- Colored exits
- Terrain indicators
- Room mood
- Weather integration (future)
- Formatted item/mob lists
"""

import logging


# Simple color helpers (expand later)
def color(text, code):
    return f"{code}{text}\033[0m"

C_EXIT = "\033[96m"     # cyan
C_TERRAIN = "\033[92m"  # green
C_MOB = "\033[93m"      # yellow
C_ITEM = "\033[95m"     # magenta
C_NAME = "\033[94m"     # blue


async def do_look(player, args):
    """Enhanced room look command."""

    room = player.room
    if not room:
        await player.send("You are floating in the void.")
        return

    # Room name
    await player.send(color(room.name, C_NAME))

    # Room description
    await player.send(room.description)

    # Terrain
    terrain = room.sector or "unknown"
    await player.send(color(f"Terrain: {terrain}", C_TERRAIN))

    # Exits
    if room.exits:
        exit_list = ", ".join(
            color(direction, C_EXIT) for direction in room.exits.keys()
        )
        await player.send(f"Exits: {exit_list}")
    else:
        await player.send("No obvious exits.")

    # Items in room
    if room.items:
        await player.send(color("You see:", C_ITEM))
        for obj in room.items:
            await player.send(f"  {color(obj.short_desc, C_ITEM)}")

    # Mobs in room
    if room.mobs:
        await player.send(color("Creatures here:", C_MOB))
        for mob in room.mobs:
            await player.send(f"  {color(mob.short_desc, C_MOB)}")


async def do_examine(player, args):
    """Examine an item or mob in the room."""

    if not args:
        await player.send("Examine what?")
        return

    target = args.lower()
    room = player.room

    # Check items
    for obj in room.items:
        if target in obj.name.lower():
            await player.send(color(obj.long_desc, C_ITEM))
            return

    # Check mobs
    for mob in room.mobs:
        if target in mob.name.lower():
            await player.send(color(mob.long_desc, C_MOB))
            return

    await player.send("You don't see that here.")


async def do_inventory(player, args):
    """Show player's inventory."""

    if not player.inventory:
        await player.send("You are carrying nothing.")
        return

    await player.send(color("You are carrying:", C_ITEM))
    for obj in player.inventory:
        await player.send(f"  {color(obj.short_desc, C_ITEM)}")


async def do_score(player, args):
    """Show player's stats."""

    await player.send(color(f"Score for {player.name}", C_NAME))
    await player.send(f"Level: {player.level}")
    await player.send(f"Race: {player.race}")
    await player.send(f"Class: {player.cls}")
    await player.send(f"HP: {player.hp}/{player.max_hp}")
    await player.send(f"Mana: {player.mana}/{player.max_mana}")
    await player.send(f"Stamina: {player.stamina}")
    await player.send(f"Gold: {player.gold}")
    await player.send(f"Experience: {player.exp}")


# Command definitions for registration
COMMAND_DEFS = [
    ("look",     do_look,     {"position": "resting", "help_category": "info"}),
    ("examine",  do_examine,  {"position": "resting", "help_category": "info"}),
    ("inventory", do_inventory, {"position": "resting", "help_category": "info"}),
    ("score",    do_score,    {"position": "resting", "help_category": "info"}),
]
