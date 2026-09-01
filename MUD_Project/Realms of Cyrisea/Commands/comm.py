"""
Realms of Cyrisea - Communication Commands
Enhanced communication:
- Colored speech
- Room broadcast formatting
- Emotes
- Tell/reply system
- Shout channel
"""

import logging

# Color codes
C_SAY = "\033[92m"      # green
C_EMOTE = "\033[95m"    # magenta
C_TELL = "\033[96m"     # cyan
C_SHOUT = "\033[93m"    # yellow
C_NAME = "\033[94m"     # blue


async def room_broadcast(room, message, exclude=None):
    """Send a message to all players in a room."""
    for player in room.players:
        if player is not exclude:
            await player.send(message)


async def do_say(player, args):
    """Speak to everyone in the room."""

    if not args:
        await player.send("Say what.")
        return

    room = player.room
    msg = f"{C_SAY}{player.name} says:{C_SAY} {args}\033[0m"

    # Player sees their own speech
    await player.send(f"{C_SAY}You say:{C_SAY} {args}\033[0m")

    # Others see it too
    await room_broadcast(room, msg, exclude=player)


async def do_emote(player, args):
    """Perform an emote visible to the room."""

    if not args:
        await player.send("Emote what.")
        return

    room = player.room
    msg = f"{C_EMOTE}{player.name} {args}\033[0m"

    await room_broadcast(room, msg)


async def do_tell(player, args):
    """Send a private message to another player."""

    if not args:
        await player.send("Tell whom what.")
        return

    parts = args.split(maxsplit=1)
    if len(parts) < 2:
        await player.send("Tell whom what.")
        return

    target_name, message = parts
    target = player.find_player_global(target_name)

    if not target:
        await player.send("They aren't here.")
        return

    # Save last tell target for reply
    player.last_tell = target
    target.last_tell = player

    await target.send(f"{C_TELL}{player.name} tells you:{C_TELL} {message}\033[0m")
    await player.send(f"{C_TELL}You tell {target.name}:{C_TELL} {message}\033[0m")


async def do_reply(player, args):
    """Reply to the last person who told you something."""

    if not player.last_tell:
        await player.send("No one has told you anything recently.")
        return

    if not args:
        await player.send("Reply what.")
        return

    target = player.last_tell

    await target.send(f"{C_TELL}{player.name} replies:{C_TELL} {args}\033[0m")
    await player.send(f"{C_TELL}You reply to {target.name}:{C_TELL} {args}\033[0m")


async def do_shout(player, args):
    """Broadcast a message globally."""

    if not args:
        await player.send("Shout what.")
        return

    msg = f"{C_SHOUT}{player.name} shouts:{C_SHOUT} {args}\033[0m"

    # Global broadcast
    for p in player.get_all_players():
        await p.send(msg)


# Command definitions
COMMAND_DEFS = [
    ("say",    do_say,    {"position": "standing", "help_category": "communication"}),
    ("emote",  do_emote,  {"position": "standing", "help_category": "communication"}),
    ("tell",   do_tell,   {"position": "standing", "help_category": "communication"}),
    ("reply",  do_reply,  {"position": "standing", "help_category": "communication"}),
    ("shout",  do_shout,  {"position": "standing", "help_category": "communication"}),
]
