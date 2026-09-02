"""
Realms of Cyrisea - Channel System
Full-featured channels:
- Global chat
- OOC chat
- RP chat
- Clan/guild channels (future)
- Party channels (future)
- Whisper
- Channel toggles
- Channel history
- Colored formatting
"""

import logging

# Channel colors
C_GLOBAL = "\033[96m"   # cyan
C_OOC    = "\033[92m"   # green
C_RP     = "\033[95m"   # magenta
C_WHIS   = "\033[94m"   # blue
C_SYS    = "\033[93m"   # yellow


# ---------------------------------------------------------
# Channel registry
# ---------------------------------------------------------

CHANNELS = {
    "global": {
        "color": C_GLOBAL,
        "history": [],
        "toggle": "global_on",
        "desc": "Global chat for all players.",
    },
    "ooc": {
        "color": C_OOC,
        "history": [],
        "toggle": "ooc_on",
        "desc": "Out-of-character chat.",
    },
    "rp": {
        "color": C_RP,
        "history": [],
        "toggle": "rp_on",
        "desc": "In-character roleplay channel.",
    },
}


# ---------------------------------------------------------
# Helper: broadcast to channel
# ---------------------------------------------------------

async def channel_broadcast(world, channel_name, message, exclude=None):
    """Send a message to all players who have the channel enabled."""

    channel = CHANNELS[channel_name]
    channel["history"].append(message)

    for p in world.players:
        if p is exclude:
            continue
        if getattr(p, channel["toggle"], True):
            await p.send(message)


# ---------------------------------------------------------
# /global
# ---------------------------------------------------------

async def do_global(player, args):
    """Speak on the global channel."""

    if not args:
        await player.send("Global what.")
        return

    if not getattr(player, "global_on", True):
        await player.send("You have the global channel turned off.")
        return

    msg = f"{C_GLOBAL}[Global] {player.name}: {args}\033[0m"
    await channel_broadcast(player.world, "global", msg)


# ---------------------------------------------------------
# /ooc
# ---------------------------------------------------------

async def do_ooc(player, args):
    """Out-of-character chat."""

    if not args:
        await player.send("OOC what.")
        return

    if not getattr(player, "ooc_on", True):
        await player.send("You have the OOC channel turned off.")
        return

    msg = f"{C_OOC}[OOC] {player.name}: {args}\033[0m"
    await channel_broadcast(player.world, "ooc", msg)


# ---------------------------------------------------------
# /rp
# ---------------------------------------------------------

async def do_rp(player, args):
    """In-character roleplay channel."""

    if not args:
        await player.send("RP what.")
        return

    if not getattr(player, "rp_on", True):
        await player.send("You have the RP channel turned off.")
        return

    msg = f"{C_RP}[RP] {player.name}: {args}\033[0m"
    await channel_broadcast(player.world, "rp", msg)


# ---------------------------------------------------------
# Whisper (private)
# ---------------------------------------------------------

async def do_whisper(player, args):
    """Whisper privately to another player."""

    parts = args.split(maxsplit=1)
    if len(parts) < 2:
        await player.send("Whisper to whom?")
        return

    target_name, message = parts
    target = player.find_player_global(target_name)

    if not target:
        await player.send("They aren't here.")
        return

    await player.send(f"{C_WHIS}You whisper to {target.name}: {message}\033[0m")
    await target.send(f"{C_WHIS}{player.name} whispers: {message}\033[0m")


# ---------------------------------------------------------
# Channel toggles
# ---------------------------------------------------------

async def do_channels(player, args):
    """Show channel status."""

    await player.send("\033[94mChannel Status:\033[0m")

    for name, data in CHANNELS.items():
        toggle = data["toggle"]
        status = "ON" if getattr(player, toggle, True) else "OFF"
        await player.send(f"{name.capitalize():10} : {status}")


async def do_channel_toggle(player, args):
    """Toggle a channel on/off."""

    if not args:
        await player.send("Toggle which channel?")
        return

    name = args.lower()
    if name not in CHANNELS:
        await player.send("No such channel.")
        return

    toggle = CHANNELS[name]["toggle"]
    current = getattr(player, toggle, True)
    setattr(player, toggle, not current)

    status = "ON" if not current else "OFF"
    await player.send(f"{name.capitalize()} channel is now {status}.")


# ---------------------------------------------------------
# Channel history
# ---------------------------------------------------------

async def do_history(player, args):
    """Show channel history."""

    if not args:
        await player.send("History for which channel?")
        return

    name = args.lower()
    if name not in CHANNELS:
        await player.send("No such channel.")
        return

    history = CHANNELS[name]["history"]

    await player.send(f"\033[94mLast messages on {name}:\033[0m")

    if not history:
        await player.send("No history yet.")
        return

    for msg in history[-20:]:
        await player.send(msg)


# ---------------------------------------------------------
# Command definitions
# ---------------------------------------------------------

COMMAND_DEFS = [
    ("global",   do_global,   {"position": "standing", "help_category": "channels"}),
    ("ooc",      do_ooc,      {"position": "standing", "help_category": "channels"}),
    ("rp",       do_rp,       {"position": "standing", "help_category": "channels"}),
    ("whisper",  do_whisper,  {"position": "standing", "help_category": "channels"}),
    ("channels", do_channels, {"position": "resting",  "help_category": "channels"}),
    ("toggle",   do_channel_toggle, {"position": "resting", "help_category": "channels"}),
    ("history",  do_history, {"position": "resting", "help_category": "channels"}),
]
