"""
Realms of Cyrisea - Mapping System
Full mapping suite:
- ASCII minimap
- Region maps
- Fog-of-war
- Auto-mapping
- Terrain symbols
- Color-coded sectors
"""

import logging

# ---------------------------------------------------------
# Sector symbols + colors
# ---------------------------------------------------------

SECTOR_SYMBOLS = {
    "field":      (".", "\033[92m"),  # green
    "forest":     ("♣", "\033[32m"),  # dark green
    "swamp":      ("≈", "\033[92m"),  # green waves
    "mountain":   ("▲", "\033[90m"),  # gray
    "cave":       ("■", "\033[37m"),  # white
    "city":       ("□", "\033[93m"),  # yellow
    "water":      ("~", "\033[94m"),  # blue
    "desert":     ("·", "\033[33m"),  # sand
    "snow":       ("*", "\033[97m"),  # white
    "unknown":    ("?", "\033[91m"),  # red
}

RESET = "\033[0m"


# ---------------------------------------------------------
# Fog-of-war tracking
# ---------------------------------------------------------

def reveal_room(player, room):
    """Mark a room as discovered."""
    player.discovered.add(room.vnum)


# ---------------------------------------------------------
# Minimap generation
# ---------------------------------------------------------

def build_minimap(player, radius=2):
    """Generate a minimap centered on the player's room."""

    world = player.world
    center = player.room

    # Build a grid of rooms around the player
    grid = {}

    # BFS search for nearby rooms
    queue = [(center, 0, 0)]
    visited = set()

    while queue:
        room, dx, dy = queue.pop(0)
        if (dx, dy) in visited:
            continue
        visited.add((dx, dy))

        grid[(dx, dy)] = room

        if abs(dx) > radius or abs(dy) > radius:
            continue

        for direction, exit in room.exits.items():
            nx, ny = dx, dy

            if direction == "north":
                ny -= 1
            elif direction == "south":
                ny += 1
            elif direction == "east":
                nx += 1
            elif direction == "west":
                nx -= 1

            queue.append((exit.destination, nx, ny))

    # Render minimap
    lines = []
    for y in range(-radius, radius + 1):
        line = ""
        for x in range(-radius, radius + 1):
            room = grid.get((x, y))
            if not room:
                line += "   "
                continue

            # Fog-of-war
            if room.vnum not in player.discovered:
                symbol, color = SECTOR_SYMBOLS["unknown"]
            else:
                symbol, color = SECTOR_SYMBOLS.get(room.sector, SECTOR_SYMBOLS["unknown"])

            # Player position
            if room == center:
                symbol = "@"
                color = "\033[96m"  # cyan

            line += f"{color}{symbol}{RESET} "
        lines.append(line)

    return lines


# ---------------------------------------------------------
# Region map (larger view)
# ---------------------------------------------------------

def build_region_map(player, area_name):
    """Render a full region map from area rooms."""

    world = player.world
    rooms = [r for r in world.rooms.values() if getattr(r, "area", None) == area_name]

    if not rooms:
        return ["No rooms found for this area."]

    # Determine bounds
    xs = []
    ys = []
    coords = {}

    for r in rooms:
        if hasattr(r, "coord"):
            x, y = r.coord
            xs.append(x)
            ys.append(y)
            coords[(x, y)] = r

    if not coords:
        return ["This area has no coordinate data."]

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    lines = []

    for y in range(min_y, max_y + 1):
        line = ""
        for x in range(min_x, max_x + 1):
            room = coords.get((x, y))
            if not room:
                line += "   "
                continue

            symbol, color = SECTOR_SYMBOLS.get(room.sector, SECTOR_SYMBOLS["unknown"])
            if room == player.room:
                symbol = "@"
                color = "\033[96m"

            line += f"{color}{symbol}{RESET} "
        lines.append(line)

    return lines


# ---------------------------------------------------------
# Commands
# ---------------------------------------------------------

async def do_map(player, args):
    """Show minimap."""

    reveal_room(player, player.room)

    lines = build_minimap(player)
    await player.send("\033[94mMinimap:\033[0m")
    for line in lines:
        await player.send(line)


async def do_region(player, args):
    """Show region map."""

    area = getattr(player.room, "area", None)
    if not area:
        await player.send("This room is not assigned to an area.")
        return

    lines = build_region_map(player, area)
    await player.send(f"\033[94mRegion Map: {area}\033[0m")
    for line in lines:
        await player.send(line)


# ---------------------------------------------------------
# Command definitions
# ---------------------------------------------------------

COMMAND_DEFS = [
    ("map",    do_map,    {"position": "standing", "help_category": "map"}),
    ("region", do_region, {"position": "standing", "help_category": "map"}),
]
