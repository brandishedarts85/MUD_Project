"""
Realms of Cyrisea - Social System
Full social suite:
- Emotes
- Custom socials
- Group/party system
- Follow/assist
- Friend lists
- Ignore lists
- RP social tools
"""

import asyncio
import logging

# ---------------------------------------------------------
# Built-in emotes
# ---------------------------------------------------------

EMOTES = {
    "smile": "smiles warmly.",
    "wave": "waves.",
    "laugh": "laughs.",
    "nod": "nods.",
    "bow": "bows respectfully.",
    "hug": "gives a warm hug.",
    "cheer": "cheers loudly!",
    "shrug": "shrugs.",
}

# ---------------------------------------------------------
# Custom socials
# ---------------------------------------------------------

CUSTOM_SOCIALS = {}  # {name: {"self": "...", "target": "..."}}

async def do_socialcreate(player, args):
    """Create a custom social."""

    parts = args.split("|")
    if len(parts) != 3:
        await player.send("Syntax: socialcreate <name>|<self>|<target>")
        return

    name, self_msg, target_msg = parts
    name = name.lower()

    CUSTOM_SOCIALS[name] = {"self": self_msg, "target": target_msg}
    await player.send(f"Custom social '{name}' created.")

# ---------------------------------------------------------
# Emote
# ---------------------------------------------------------

async def do_emote(player, args):
    """Perform an emote."""

    if not args:
        await player.send("Emote what.")
        return

    await player.room.broadcast(f"{player.name} {args}", exclude=None)

# ---------------------------------------------------------
# Social
# ---------------------------------------------------------

async def do_social(player, args):
    """Use a social action."""

    parts = args.split(maxsplit=1)
    name = parts[0].lower()

    # Built-in emote
    if name in EMOTES:
        msg = EMOTES[name]
        await player.room.broadcast(f"{player.name} {msg}")
        return

    # Custom social
    if name in CUSTOM_SOCIALS:
        social = CUSTOM_SOCIALS[name]

        if len(parts) == 1:
            # No target
            await player.room.broadcast(f"{player.name} {social['self']}")
            return

        target_name = parts[1]
        target = player.room.find_player(target_name)

        if not target:
            await player.send("They aren't here.")
            return

        await player.send(f"You {social['self']} at {target.name}.")
        await target.send(f"{player.name} {social['target']} at you.")
        await player.room.broadcast(
            f"{player.name} {social['self']} at {target.name}.",
            exclude=[player, target]
        )
        return

    await player.send("No such social.")

# ---------------------------------------------------------
# Friend list
# ---------------------------------------------------------

async def do_friend(player, args):
    """Add or remove a friend."""

    if not args:
        await player.send("Friends: " + ", ".join(player.friends))
        return

    parts = args.split()
    if len(parts) != 2:
        await player.send("Syntax: friend <add/remove> <name>")
        return

    action, name = parts
    name = name.lower()

    if action == "add":
        player.friends.add(name)
        await player.send(f"{name} added to your friends list.")
    elif action == "remove":
        player.friends.discard(name)
        await player.send(f"{name} removed from your friends list.")
    else:
        await player.send("Use add/remove.")

# ---------------------------------------------------------
# Ignore list
# ---------------------------------------------------------

async def do_ignore(player, args):
    """Add or remove someone from ignore list."""

    if not args:
        await player.send("Ignored: " + ", ".join(player.ignored))
        return

    parts = args.split()
    if len(parts) != 2:
        await player.send("Syntax: ignore <add/remove> <name>")
        return

    action, name = parts
    name = name.lower()

    if action == "add":
        player.ignored.add(name)
        await player.send(f"You now ignore {name}.")
    elif action == "remove":
        player.ignored.discard(name)
        await player.send(f"You no longer ignore {name}.")
    else:
        await player.send("Use add/remove.")

# ---------------------------------------------------------
# Follow
# ---------------------------------------------------------

async def do_follow(player, args):
    """Follow another player."""

    if not args:
        await player.send("Follow whom.")
        return

    target = player.room.find_player(args)
    if not target:
        await player.send("They aren't here.")
        return

    player.following = target
    await player.send(f"You follow {target.name}.")
    await target.send(f"{player.name} begins following you.")

# ---------------------------------------------------------
# Assist
# ---------------------------------------------------------

async def do_assist(player, args):
    """Assist someone in combat."""

    if not args:
        await player.send("Assist whom.")
        return

    target = player.room.find_player(args)
    if not target:
        await player.send("They aren't here.")
        return

    if not target.fighting:
        await player.send("They are not fighting.")
        return

    enemy = target.fighting
    player.fighting = enemy
    enemy.fighting = player

    await player.send(f"You assist {target.name}!")
    await target.send(f"{player.name} assists you!")
    await enemy.send(f"{player.name} joins the fight against you!")

# ---------------------------------------------------------
# Party system
# ---------------------------------------------------------

async def do_party(player, args):
    """Party commands."""

    parts = args.split(maxsplit=1)
    if not parts:
        await player.send("Party commands: create, invite, leave, list")
        return

    cmd = parts[0]

    # Create party
    if cmd == "create":
        if player.party:
            await player.send("You are already in a party.")
            return
        player.party = {"leader": player, "members": {player}}
        await player.send("Party created.")
        return

    # Invite
    if cmd == "invite":
        if not player.party or player.party["leader"] != player:
            await player.send("You are not the party leader.")
            return

        target_name = parts[1]
        target = player.room.find_player(target_name)
        if not target:
            await player.send("They aren't here.")
            return

        target.party_invite = player.party
        await player.send(f"You invite {target.name} to your party.")
        await target.send(f"{player.name} invites you to join their party.")
        return

    # Leave
    if cmd == "leave":
        if not player.party:
            await player.send("You are not in a party.")
            return

        party = player.party
        party["members"].discard(player)
        player.party = None

        await player.send("You leave the party.")
        return

    # List
    if cmd == "list":
        if not player.party:
            await player.send("You are not in a party.")
            return

        await player.send("Party members:")
        for m in player.party["members"]:
            await player.send(f" - {m.name}")
        return

    await player.send("Unknown party command.")

async def do_acceptparty(player, args):
    """Accept a party invite."""

    party = getattr(player, "party_invite", None)
    if not party:
        await player.send("No party invite to accept.")
        return

    party["members"].add(player)
    player.party = party
    player.party_invite = None

    await player.send("You join the party.")
    for m in party["members"]:
        await m.send(f"{player.name} joins the party.")

COMMAND_DEFS = [
    ("emote",       do_emote,       {"position": "standing", "help_category": "social"}),
    ("social",      do_social,      {"position": "standing", "help_category": "social"}),
    ("socialcreate",do_socialcreate,{"position": "standing", "help_category": "social"}),
    ("friend",      do_friend,      {"position": "standing", "help_category": "social"}),
    ("ignore",      do_ignore,      {"position": "standing", "help_category": "social"}),
    ("follow",      do_follow,      {"position": "standing", "help_category": "social"}),
    ("assist",      do_assist,      {"position": "standing", "help_category": "social"}),
    ("party",       do_party,       {"position": "standing", "help_category": "social"}),
    ("acceptparty", do_acceptparty, {"position": "standing", "help_category": "social"}),
]
