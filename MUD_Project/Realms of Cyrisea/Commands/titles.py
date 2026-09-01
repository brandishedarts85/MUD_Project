"""
Realms of Cyrisea - Title System
Full title suite:
- Title unlocks
- Title categories
- Title rarity tiers
- Title bonuses
- Achievement titles
- Faction/guild titles
- Cosmetic titles
"""

import asyncio
import logging

# ---------------------------------------------------------
# Title rarity tiers
# ---------------------------------------------------------

TITLE_RARITY = {
    "common": 1,
    "uncommon": 2,
    "rare": 3,
    "epic": 4,
    "legendary": 5,
}

# ---------------------------------------------------------
# Title categories
# ---------------------------------------------------------

TITLE_CATEGORIES = {
    "achievement": "Achievement Titles",
    "faction": "Faction Titles",
    "guild": "Guild Titles",
    "combat": "Combat Titles",
    "exploration": "Exploration Titles",
    "pets": "Pet Titles",
    "housing": "Housing Titles",
    "events": "Event Titles",
    "cosmetic": "Cosmetic Titles",
}

# ---------------------------------------------------------
# Title registry
# ---------------------------------------------------------

TITLES = {
    # Achievement titles
    "first_blood": {
        "name": "The Initiate",
        "category": "achievement",
        "rarity": "common",
        "unlock": {"achievement": "first_blood"},
        "bonus": {},
    },
    "slayer_100": {
        "name": "Hundred Slayer",
        "category": "achievement",
        "rarity": "rare",
        "unlock": {"achievement": "slayer_100"},
        "bonus": {"attack": 2},
    },

    # Faction titles
    "crystalwood_warden": {
        "name": "Warden of Crystalwood",
        "category": "faction",
        "rarity": "epic",
        "unlock": {"faction_rank": {"faction": "crystalwood", "rank": "Warden"}},
        "bonus": {"dodge": 5},
    },
    "obsidian_archon": {
        "name": "Obsidian Archon",
        "category": "faction",
        "rarity": "legendary",
        "unlock": {"faction_rank": {"faction": "obsidian_order", "rank": "Obsidian Archon"}},
        "bonus": {"magic": 5},
    },

    # Guild titles
    "guild_leader": {
        "name": "Guildmaster",
        "category": "guild",
        "rarity": "epic",
        "unlock": {"guild_rank": "Leader"},
        "bonus": {"leadership": 10},
    },
    "guild_officer": {
        "name": "Guild Officer",
        "category": "guild",
        "rarity": "rare",
        "unlock": {"guild_rank": "Officer"},
        "bonus": {"charisma": 3},
    },

    # Combat titles
    "boss_slayer": {
        "name": "Colossus Slayer",
        "category": "combat",
        "rarity": "epic",
        "unlock": {"kill": {"target": 9500}},
        "bonus": {"attack": 3},
    },

    # Exploration titles
    "worldwalker": {
        "name": "Worldwalker",
        "category": "exploration",
        "rarity": "rare",
        "unlock": {"achievement": "worldwalker"},
        "bonus": {"movement": 1},
    },

    # Pet titles
    "pet_master": {
        "name": "Beastmaster",
        "category": "pets",
        "rarity": "epic",
        "unlock": {"pet_level": 10},
        "bonus": {"pet_power": 5},
    },

    # Housing titles
    "homeowner": {
        "name": "Homesteader",
        "category": "housing",
        "rarity": "common",
        "unlock": {"achievement": "homeowner"},
        "bonus": {},
    },

    # Event titles
    "event_defender": {
        "name": "Defender of the Glade",
        "category": "events",
        "rarity": "rare",
        "unlock": {"achievement": "event_defender"},
        "bonus": {"defense": 2},
    },

    # Cosmetic titles
    "wanderer": {
        "name": "The Wanderer",
        "category": "cosmetic",
        "rarity": "common",
        "unlock": {"free": True},
        "bonus": {},
    },
}

# ---------------------------------------------------------
# Player title state
# ---------------------------------------------------------

def unlock_title(player, title_id):
    if title_id not in player.titles:
        player.titles.add(title_id)
        return True
    return False

def set_active_title(player, title_id):
    if title_id in player.titles:
        player.active_title = title_id
        return True
    return False

# ---------------------------------------------------------
# Title unlock logic
# ---------------------------------------------------------

async def check_title_unlocks(player, trigger_type, value=None):
    for tid, tdef in TITLES.items():
        unlock = tdef["unlock"]

        # Free titles
        if unlock.get("free"):
            await grant_title(player, tid)
            continue

        # Achievement titles
        if trigger_type == "achievement" and unlock.get("achievement") == value:
            await grant_title(player, tid)

        # Faction rank titles
        if trigger_type == "faction_rank":
            fr = unlock.get("faction_rank")
            if fr and fr["faction"] == value["faction"] and fr["rank"] == value["rank"]:
                await grant_title(player, tid)

        # Guild rank titles
        if trigger_type == "guild_rank":
            if unlock.get("guild_rank") == value:
                await grant_title(player, tid)

        # Kill-based titles
        if trigger_type == "kill" and unlock.get("kill"):
            if unlock["kill"]["target"] == value:
                await grant_title(player, tid)

        # Pet level titles
        if trigger_type == "pet_level":
            if unlock.get("pet_level") == value:
                await grant_title(player, tid)

# ---------------------------------------------------------
# Grant title
# ---------------------------------------------------------

async def grant_title(player, title_id):
    if not unlock_title(player, title_id):
        return

    tdef = TITLES[title_id]
    await player.send("\033[94mTitle Unlocked!\033[0m")
    await player.send(f"{tdef['name']} — {tdef['desc'] if 'desc' in tdef else ''}")

    # Apply bonuses
    for stat, value in tdef.get("bonus", {}).items():
        player.stats[stat] = player.stats.get(stat, 0) + value

async def do_titles(player, args):
    """List unlocked titles."""

    if not player.titles:
        await player.send("You have no titles unlocked.")
        return

    await player.send("\033[95mUnlocked Titles:\033[0m")
    for tid in player.titles:
        tdef = TITLES[tid]
        await player.send(f"{tdef['name']} ({tdef['category']}, {tdef['rarity']})")

async def do_title(player, args):
    """Show title details."""

    if not args:
        await player.send("Title which?")
        return

    tid = args.lower()
    if tid not in TITLES:
        await player.send("No such title.")
        return

    tdef = TITLES[tid]

    await player.send(f"\033[94m{tdef['name']}\033[0m")
    await player.send(f"Category: {TITLE_CATEGORIES[tdef['category']]}")
    await player.send(f"Rarity: {tdef['rarity'].title()}")
    if tdef.get("bonus"):
        await player.send("Bonuses:")
        for stat, val in tdef["bonus"].items():
            await player.send(f" - {stat}: +{val}")

async def do_settitle(player, args):
    """Set your active title."""

    if not args:
        await player.send("Set which title?")
        return

    tid = args.lower()
    if tid not in player.titles:
        await player.send("You have not unlocked that title.")
        return

    set_active_title(player, tid)
    await player.send(f"Your title is now: {TITLES[tid]['name']}")

COMMAND_DEFS = [
    ("titles",    do_titles,    {"position": "standing", "help_category": "titles"}),
    ("title",     do_title,     {"position": "standing", "help_category": "titles"}),
    ("settitle",  do_settitle,  {"position": "standing", "help_category": "titles"}),
]
