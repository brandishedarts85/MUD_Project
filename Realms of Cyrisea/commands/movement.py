"""
Realms of Cyrisea - Movement Commands
Enhanced movement system:
- Terrain-based movement cost
- Stamina system
- Exhaustion
- Room transitions
"""

import logging

# Terrain movement cost table
TERRAIN_COST = {
    "road": 1,
    "field": 2,
    "forest": 3,
    "swamp": 4,
    "mountain": 5,
    "water": 6,
    "desert": 4,
    "city": 1,
    "indoors": 1,
}

# Exhaustion threshold
EXHAUSTION_LIMIT = 5


async def move_player(player, direction):
    """Core movement logic shared by all directional commands."""

    room = player.room
    if not room:
        await player.send("You are nowhere. Movement is impossible.")
        return

    exit_data = room.exits.get(direction)
    if not exit_data:
        await player.send("You can't go that way.")
        return

    dest_room = exit_data.destination
    if not dest_room:
        await player.send("That exit leads nowhere.")
        return

    # Terrain cost
    terrain = dest_room.sector or "field"
    cost = TERRAIN_COST.get(terrain, 2)

    # Check stamina
    if player.stamina < cost:
        await player.send("You are too exhausted to move.")
        return

    # Apply movement cost
    player.stamina -= cost
    player.exhaustion += 1

    # Exhaustion feedback
    if player.exhaustion >= EXHAUSTION_LIMIT:
        await player.send("You feel exhausted.")
        player.exhaustion = 0

    # Move player
    player.room = dest_room
    await player.send(f"You walk {direction}.")
    await player.send(dest_room.description)

    # Notify others (optional)
    # await room.broadcast(f"{player.name} leaves {direction}.", exclude=player)
    # await dest_room.broadcast(f"{player.name} arrives.", exclude=player)


# Direction commands
async def do_north(player, args):
    await move_player(player, "north")

async def do_south(player, args):
    await move_player(player, "south")

async def do_east(player, args):
    await move_player(player, "east")

async def do_west(player, args):
    await move_player(player, "west")

async def do_up(player, args):
    await move_player(player, "up")

async def do_down(player, args):
    await move_player(player, "down")


# Command definitions for registration
COMMAND_DEFS = [
    ("north", do_north, {"position": "standing", "help_category": "movement"}),
    ("south", do_south, {"position": "standing", "help_category": "movement"}),
    ("east",  do_east,  {"position": "standing", "help_category": "movement"}),
    ("west",  do_west,  {"position": "standing", "help_category": "movement"}),
    ("up",    do_up,    {"position": "standing", "help_category": "movement"}),
    ("down",  do_down,  {"position": "standing", "help_category": "movement"}),
]
