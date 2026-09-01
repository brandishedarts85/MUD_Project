"""
Realms of Cyrisea - WHO List
Enhanced WHO system:
- Colored names
- Level/class/race display
- Admin badges
- Room location
- Sorting
- Optional anonymous mode
"""

import logging

C_TITLE = "\033[95m"   # magenta
C_NAME  = "\033[96m"   # cyan
C_ADMIN = "\033[93m"   # yellow
C_TEXT  = "\033[37m"   # white


ADMIN_TITLES = {
    0: "",
    1: "[Builder]",
    2: "[Guide]",
    3: "[Moderator]",
    4: "[Immortal]",
    5: "[Overseer]",
    6: "[Archon]",
    7: "[Celestial]",
    8: "[Eternal]",
    9: "[Ascendant]",
    10: "[God]",
}


async def do_who(player, args):
    """Show all connected players."""

    world = player.world
    players = world.players

    # Sorting options
    if args == "level":
        players = sorted(players, key=lambda p: p.level, reverse=True)
    elif args == "name":
        players = sorted(players, key=lambda p: p.name.lower())
    elif args == "race":
        players = sorted(players, key=lambda p: p.race.lower())
    elif args == "class":
        players = sorted(players, key=lambda p: p.cls.lower())

    await player.send(f"{C_TITLE}Players Online:\033[0m")

    if not players:
        await player.send("No one is currently online.")
        return

    for p in players:
        # Admin badge
        badge = ADMIN_TITLES.get(p.admin, "")

        # Name formatting
        name = f"{C_NAME}{p.name}\033[0m"

        # Anonymous mode (future feature)
        if getattr(p, "anonymous", False):
            name = f"{C_NAME}(anonymous)\033[0m"

        # Location
        loc = p.room.name if p.room else "Unknown"

        # Build line
        line = (
            f"{name:20} "
            f"Lv {p.level:<2} "
            f"{p.race.capitalize():10} "
            f"{p.cls.capitalize():10} "
            f"{C_ADMIN}{badge:12}\033[0m "
            f"{C_TEXT}{loc}\033[0m"
        )

        await player.send(line)


async def do_whois(player, args):
    """Show detailed info about a single player."""

    if not args:
        await player.send("Whois whom.")
        return

    target = player.find_player_global(args)
    if not target:
        await player.send("They aren't online.")
        return

    await player.send(f"{C_TITLE}Whois: {target.name}\033[0m")

    await player.send(f"Level: {target.level}")
    await player.send(f"Race: {target.race}")
    await player.send(f"Class: {target.cls}")
    await player.send(f"HP: {target.hp}/{target.max_hp}")
    await player.send(f"Mana: {target.mana}/{target.max_mana}")
    await player.send(f"Stamina: {target.stamina}/{target.max_stamina}")
    await player.send(f"Gold: {target.gold}")
    await player.send(f"Experience: {target.exp}")

    badge = ADMIN_TITLES.get(target.admin, "")
    if badge:
        await player.send(f"Admin: {badge}")

    loc = target.room.name if target.room else "Unknown"
    await player.send(f"Location: {loc}")


# Command definitions
COMMAND_DEFS = [
    ("who",   do_who,   {"position": "resting", "help_category": "info"}),
    ("whois", do_whois, {"position": "resting", "help_category": "info"}),
]
