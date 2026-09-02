"""
Realms of Cyrisea - Guild System
Full guild suite:
- Guild creation
- Guild ranks
- Guild permissions
- Guild halls
- Guild storage
- Guild crafting stations
- Guild quests
- Guild events
- Guild warfare
"""

import asyncio
import logging
import random

# ---------------------------------------------------------
# Guild ranks
# ---------------------------------------------------------

GUILD_RANKS = [
    "Recruit",
    "Member",
    "Officer",
    "Council",
    "Leader",
]

# ---------------------------------------------------------
# Guild registry
# ---------------------------------------------------------

GUILDS = {}  # {guild_name: guild_data}


def create_guild_instance(world, guild_name):
    """Create an instanced guild hall."""

    base_vnum = world.next_instance_vnum
    world.next_instance_vnum += 200

    hall = world.create_room(base_vnum, f"{guild_name} Hall", "")
    hall.is_guildhall = True
    hall.guild = guild_name
    hall.storage = []
    hall.stations = []
    hall.meeting_room = world.create_room(
        base_vnum + 1,
        f"{guild_name} Council Chamber",
        "",
    )
    hall.meeting_room.guild = guild_name
    hall.meeting_room.is_guildhall = True

    hall.add_exit("north", hall.meeting_room)
    hall.meeting_room.add_exit("south", hall)

    return {
        "hall": hall,
        "meeting": hall.meeting_room,
        "members": {},
        "storage": [],
        "stations": [],
        "quests": [],
        "events": [],
        "war_state": None,
    }


# ---------------------------------------------------------
# Create guild
# ---------------------------------------------------------

async def do_guildcreate(player, args):
    """Create a new guild."""

    if player.guild:
        await player.send("You are already in a guild.")
        return

    if not args:
        await player.send("Guild name required.")
        return

    name = args.title()

    if name in GUILDS:
        await player.send("A guild with that name already exists.")
        return

    # Cost to create a guild
    cost = 5000
    if player.gold < cost:
        await player.send("You cannot afford to create a guild.")
        return

    player.gold -= cost

    instance = create_guild_instance(player.world, name)
    GUILDS[name] = instance

    # Add creator as leader
    instance["members"][player.name] = "Leader"
    player.guild = name
    player.guild_rank = "Leader"

    await player.send(f"You create the guild {name}!")


# ---------------------------------------------------------
# Guild information
# ---------------------------------------------------------

async def do_guild(player, args):
    """Show guild info."""

    if not player.guild:
        await player.send("You are not in a guild.")
        return

    guild = GUILDS[player.guild]

    await player.send(f"\033[95mGuild: {player.guild}\033[0m")
    await player.send(f"Rank: {player.guild_rank}")
    await player.send("Members:")

    for m, r in guild["members"].items():
        await player.send(f" - {m} ({r})")


# ---------------------------------------------------------
# Guild invitations
# ---------------------------------------------------------

async def do_ginvite(player, args):
    """Invite someone to your guild."""

    if not player.guild or player.guild_rank not in [
        "Officer",
        "Council",
        "Leader",
    ]:
        await player.send("You do not have permission.")
        return

    target = player.room.find_player(args)

    if not target:
        await player.send("They aren't here.")
        return

    if target.guild:
        await player.send("They are already in a guild.")
        return

    target.guild_invite = player.guild

    await player.send(
        f"You invite {target.name} to join {player.guild}."
    )

    await target.send(
        f"{player.name} invites you to join the guild {player.guild}."
    )


# ---------------------------------------------------------
# Guild acceptance
# ---------------------------------------------------------

async def do_gaccept(player, args):
    """Accept a guild invite."""

    guild_name = getattr(player, "guild_invite", None)

    if not guild_name:
        await player.send("No guild invite to accept.")
        return

    guild = GUILDS.get(guild_name)

    if not guild:
        player.guild_invite = None
        await player.send("That guild no longer exists.")
        return

    guild["members"][player.name] = "Recruit"
    player.guild = guild_name
    player.guild_rank = "Recruit"
    player.guild_invite = None

    await player.send(f"You join the guild {guild_name}.")

    for m in guild["members"]:
        if m == player.name:
            continue

        member = player.world.find_player_global(m)

        if member:
            await member.send(f"{player.name} joins the guild.")


# ---------------------------------------------------------
# Guild promotion
# ---------------------------------------------------------

async def do_gpromote(player, args):
    """Promote a guild member."""

    if not player.guild or player.guild_rank not in [
        "Council",
        "Leader",
    ]:
        await player.send("You do not have permission.")
        return

    guild = GUILDS[player.guild]
    target_name = args.strip()

    if not target_name:
        await player.send("Promote whom?")
        return

    target_rank = guild["members"].get(target_name)

    if not target_rank:
        await player.send("No such guild member.")
        return

    current_rank = target_rank
    idx = GUILD_RANKS.index(current_rank)

    if idx >= len(GUILD_RANKS) - 1:
        await player.send("They cannot be promoted further.")
        return

    new_rank = GUILD_RANKS[idx + 1]
    guild["members"][target_name] = new_rank

    target = player.world.find_player_global(target_name)

    if target:
        target.guild_rank = new_rank
        await target.send(
            f"You have been promoted to {new_rank}."
        )

    await player.send(
        f"You promote {target_name} to {new_rank}."
    )


# ---------------------------------------------------------
# Guild storage
# ---------------------------------------------------------

async def do_gstore(player, args):
    """Store an item in guild storage."""

    if not player.guild:
        await player.send("You are not in a guild.")
        return

    if player.guild_rank not in [
        "Officer",
        "Council",
        "Leader",
    ]:
        await player.send(
            "You do not have permission to store items in the guild vault."
        )
        return

    item_name = args.strip().lower()

    if not item_name:
        await player.send("Store what?")
        return

    guild = GUILDS[player.guild]

    for obj in list(player.inventory):
        short_desc = getattr(obj, "short_desc", None)

        if not short_desc:
            short_desc = getattr(obj, "name", "")

        if item_name in short_desc.lower():
            player.inventory.remove(obj)
            guild["storage"].append(obj)

            await player.send(
                f"You store {short_desc} in the guild vault."
            )
            return

    await player.send("You do not have that item.")


# ---------------------------------------------------------
# Guild storage retrieval
# ---------------------------------------------------------

async def do_gretrieve(player, args):
    """Retrieve an item from guild storage."""

    if not player.guild:
        await player.send("You are not in a guild.")
        return

    item_name = args.strip().lower()

    if not item_name:
        await player.send("Retrieve what?")
        return

    guild = GUILDS[player.guild]

    for obj in list(guild["storage"]):
        short_desc = getattr(obj, "short_desc", None)

        if not short_desc:
            short_desc = getattr(obj, "name", "")

        if item_name in short_desc.lower():
            guild["storage"].remove(obj)
            player.inventory.append(obj)

            await player.send(
                f"You retrieve {short_desc} from the guild vault."
            )
            return

    await player.send("No such item in guild storage.")


# ---------------------------------------------------------
# Guild crafting stations
# ---------------------------------------------------------

async def do_ginstall(player, args):
    """Install a crafting station in the guild hall."""

    if not player.guild or player.guild_rank not in [
        "Officer",
        "Council",
        "Leader",
    ]:
        await player.send("You do not have permission.")
        return

    room = player.room

    if not room.is_guildhall or room.guild != player.guild:
        await player.send("You must be in your guild hall.")
        return

    station_name = args.lower()

    for obj in list(player.inventory):
        if (
            getattr(obj, "is_station", False)
            and station_name in getattr(
                obj,
                "short_desc",
                getattr(obj, "name", ""),
            ).lower()
        ):
            player.inventory.remove(obj)

            GUILDS[player.guild]["stations"].append(
                obj.station_type
            )

            await player.send(
                f"You install {obj.short_desc} in the guild hall."
            )
            return

    await player.send("You do not have that station.")


# ---------------------------------------------------------
# Guild quests
# ---------------------------------------------------------

async def do_gquests(player, args):
    """List guild quests."""

    if not player.guild:
        await player.send("You are not in a guild.")
        return

    guild = GUILDS[player.guild]

    if not guild["quests"]:
        await player.send("Your guild has no active quests.")
        return

    await player.send("\033[94mGuild Quests:\033[0m")

    for q in guild["quests"]:
        await player.send(
            f" - {q['name']}: {q['desc']}"
        )


# ---------------------------------------------------------
# Guild events
# ---------------------------------------------------------

async def do_gevents(player, args):
    """List guild events."""

    if not player.guild:
        await player.send("You are not in a guild.")
        return

    guild = GUILDS[player.guild]

    if not guild["events"]:
        await player.send("Your guild has no active events.")
        return

    await player.send("\033[95mGuild Events:\033[0m")

    for e in guild["events"]:
        await player.send(
            f" - {e['name']}: {e['desc']}"
        )


# ---------------------------------------------------------
# Guild warfare
# ---------------------------------------------------------

async def do_gwar(player, args):
    """Declare guild war."""

    if not player.guild or player.guild_rank != "Leader":
        await player.send(
            "Only guild leaders may declare war."
        )
        return

    target_name = args.title()

    if target_name not in GUILDS:
        await player.send("No such guild.")
        return

    if target_name == player.guild:
        await player.send(
            "You cannot declare war on your own guild."
        )
        return

    GUILDS[player.guild]["war_state"] = target_name
    GUILDS[target_name]["war_state"] = player.guild

    await player.send(
        f"You declare war on {target_name}."
    )

    for m in GUILDS[target_name]["members"]:
        p = player.world.find_player_global(m)

        if p:
            await p.send(
                f"{player.guild} has declared war on your guild!"
            )


# ---------------------------------------------------------
# Command registration
# ---------------------------------------------------------

COMMAND_DEFS = [
    (
        "guildcreate",
        do_guildcreate,
        {"position": "standing", "help_category": "guilds"},
    ),
    (
        "guild",
        do_guild,
        {"position": "standing", "help_category": "guilds"},
    ),
    (
        "ginvite",
        do_ginvite,
        {"position": "standing", "help_category": "guilds"},
    ),
    (
        "gaccept",
        do_gaccept,
        {"position": "standing", "help_category": "guilds"},
    ),
    (
        "gpromote",
        do_gpromote,
        {"position": "standing", "help_category": "guilds"},
    ),
    (
        "gstore",
        do_gstore,
        {"position": "standing", "help_category": "guilds"},
    ),
    (
        "gretrieve",
        do_gretrieve,
        {"position": "standing", "help_category": "guilds"},
    ),
    (
        "ginstall",
        do_ginstall,
        {"position": "standing", "help_category": "guilds"},
    ),
    (
        "gquests",
        do_gquests,
        {"position": "standing", "help_category": "guilds"},
    ),
    (
        "gevents",
        do_gevents,
        {"position": "standing", "help_category": "guilds"},
    ),
    (
        "gwar",
        do_gwar,
        {"position": "standing", "help_category": "guilds"},
    ),
]
