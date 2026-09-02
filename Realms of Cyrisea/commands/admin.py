"""
Realms of Cyrisea - Admin Commands
Enhanced admin suite:
- Tiered admin levels
- Safe-mode commands
- Logging
- Anti-abuse checks
- World editing hooks
- Mob/object spawning
- Room editing
- Player moderation tools
"""

import logging
import asyncio


# ---------------------------------------------------------
# Admin level requirements
# ---------------------------------------------------------

ADMIN_LEVELS = {
    "builder": 1,
    "guide": 2,
    "moderator": 3,
    "immortal": 4,
    "overseer": 5,
    "archon": 6,
    "celestial": 7,
    "eternal": 8,
    "ascendant": 9,
    "god": 10,
}


def require_admin(player, level):
    """Check admin level."""
    if player.admin < level:
        return False
    return True


# ---------------------------------------------------------
# ADVANCE (level up a player)
# ---------------------------------------------------------

async def do_advance(player, args):
    """Advance a player's level."""

    if not require_admin(player, ADMIN_LEVELS["immortal"]):
        await player.send("You do not have permission.")
        return

    parts = args.split()
    if len(parts) != 2:
        await player.send("Syntax: advance <player> <level>")
        return

    target_name, level_str = parts
    target = player.find_player_global(target_name)

    if not target:
        await player.send("They aren't online.")
        return

    try:
        level = int(level_str)
    except ValueError:
        await player.send("Level must be a number.")
        return

    target.level = level
    await player.send(f"You advance {target.name} to level {level}.")
    await target.send(f"Your level has been set to {level} by {player.name}.")


# ---------------------------------------------------------
# RESTORE (heal a player)
# ---------------------------------------------------------

async def do_restore(player, args):
    """Restore a player's HP/Mana/Stamina."""

    if not require_admin(player, ADMIN_LEVELS["guide"]):
        await player.send("You do not have permission.")
        return

    target = player.find_player_global(args)
    if not target:
        await player.send("They aren't online.")
        return

    target.hp = target.max_hp
    target.mana = target.max_mana
    target.stamina = target.max_stamina

    await player.send(f"You restore {target.name}.")
    await target.send("You feel fully restored.")


# ---------------------------------------------------------
# FORCE (make a player execute a command)
# ---------------------------------------------------------

async def do_force(player, args):
    """Force a player to execute a command."""

    if not require_admin(player, ADMIN_LEVELS["moderator"]):
        await player.send("You do not have permission.")
        return

    parts = args.split(maxsplit=1)
    if len(parts) != 2:
        await player.send("Syntax: force <player> <command>")
        return

    target_name, command = parts
    target = player.find_player_global(target_name)

    if not target:
        await player.send("They aren't online.")
        return

    await player.send(f"You force {target.name} to: {command}")
    await target.send(f"{player.name} forces you to: {command}")

    # Execute forced command
    cmd, cmd_args = target.world.server.parse_command(command)
    if cmd:
        await target.world.server.execute_command(target, cmd, cmd_args)


# ---------------------------------------------------------
# GOTO (teleport to a room)
# ---------------------------------------------------------

async def do_goto(player, args):
    """Teleport to a room by vnum."""

    if not require_admin(player, ADMIN_LEVELS["immortal"]):
        await player.send("You do not have permission.")
        return

    try:
        vnum = int(args)
    except ValueError:
        await player.send("Room vnum must be a number.")
        return

    room = player.world.rooms.get(vnum)
    if not room:
        await player.send("No such room.")
        return

    # Leave current room
    if player.room:
        await player.room.leave(player)

    # Enter new room
    await room.enter(player)
    await player.send(f"You teleport to room {vnum}.")


# ---------------------------------------------------------
# SUMMON (bring a player to you)
# ---------------------------------------------------------

async def do_summon(player, args):
    """Summon a player to your room."""

    if not require_admin(player, ADMIN_LEVELS["immortal"]):
        await player.send("You do not have permission.")
        return

    target = player.find_player_global(args)
    if not target:
        await player.send("They aren't online.")
        return

    # Move target
    if target.room:
        await target.room.leave(target)

    await player.room.enter(target)

    await player.send(f"You summon {target.name}.")
    await target.send("You are summoned by an immortal!")


# ---------------------------------------------------------
# SET (modify player stats)
# ---------------------------------------------------------

async def do_set(player, args):
    """Set a player's stat."""

    if not require_admin(player, ADMIN_LEVELS["overseer"]):
        await player.send("You do not have permission.")
        return

    parts = args.split()
    if len(parts) != 3:
        await player.send("Syntax: set <player> <field> <value>")
        return

    target_name, field, value = parts
    target = player.find_player_global(target_name)

    if not target:
        await player.send("They aren't online.")
        return

    if not hasattr(target, field):
        await player.send("Invalid field.")
        return

    try:
        value = int(value)
    except ValueError:
        await player.send("Value must be a number.")
        return

    setattr(target, field, value)
    await player.send(f"You set {target.name}'s {field} to {value}.")
    await target.send(f"Your {field} has been set to {value}.")


# ---------------------------------------------------------
# SPAWN MOB
# ---------------------------------------------------------

async def do_spawnmob(player, args):
    """Spawn a mob by vnum."""

    if not require_admin(player, ADMIN_LEVELS["archon"]):
        await player.send("You do not have permission.")
        return

    try:
        vnum = int(args)
    except ValueError:
        await player.send("Mob vnum must be a number.")
        return

    mob_template = player.world.mobs.get(vnum)
    if not mob_template:
        await player.send("No such mob.")
        return

    mob = mob_template.clone()
    mob.spawn(player.room)

    await player.send(f"You spawn {mob.name}.")
    await player.room.broadcast(f"{mob.name} materializes!", exclude=player)


# ---------------------------------------------------------
# SPAWN OBJECT
# ---------------------------------------------------------

async def do_spawnobj(player, args):
    """Spawn an object by vnum."""

    if not require_admin(player, ADMIN_LEVELS["archon"]):
        await player.send("You do not have permission.")
        return

    try:
        vnum = int(args)
    except ValueError:
        await player.send("Object vnum must be a number.")
        return

    obj_template = player.world.objects.get(vnum)
    if not obj_template:
        await player.send("No such object.")
        return

    obj = obj_template.clone()
    player.room.items.append(obj)

    await player.send(f"You spawn {obj.short_desc}.")
    await player.room.broadcast(f"{obj.short_desc} appears!", exclude=player)


# ---------------------------------------------------------
# SHUTDOWN
# ---------------------------------------------------------

async def do_shutdown(player, args):
    """Shutdown the server."""

    if not require_admin(player, ADMIN_LEVELS["god"]):
        await player.send("You do not have permission.")
        return

    await player.send("Server shutting down.")
    logging.info("Shutdown initiated by admin.")

    # Graceful shutdown
    player.world.server.running = False

    for session in player.world.server.sessions:
        await session.send("Server is shutting down.")
        await session.close()


# ---------------------------------------------------------
# Command definitions
# ---------------------------------------------------------

COMMAND_DEFS = [
    ("advance",  do_advance,  {"position": "standing", "help_category": "admin", "admin": 4}),
    ("restore",  do_restore,  {"position": "standing", "help_category": "admin", "admin": 2}),
    ("force",    do_force,    {"position": "standing", "help_category": "admin", "admin": 3}),
    ("goto",     do_goto,     {"position": "standing", "help_category": "admin", "admin": 4}),
    ("summon",   do_summon,   {"position": "standing", "help_category": "admin", "admin": 4}),
    ("set",      do_set,      {"position": "standing", "help_category": "admin", "admin": 5}),
    ("spawnmob", do_spawnmob, {"position": "standing", "help_category": "admin", "admin": 6}),
    ("spawnobj", do_spawnobj, {"position": "standing", "help_category": "admin", "admin": 6}),
    ("shutdown", do_shutdown, {"position": "standing", "help_category": "admin", "admin": 10}),
]
