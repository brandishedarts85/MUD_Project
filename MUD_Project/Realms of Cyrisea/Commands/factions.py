"""
Realms of Cyrisea - Faction System
Full-featured factions:
- Faction definitions
- Reputation
- Ranks
- Faction quests
- Faction shops
- Faction abilities
- Faction storylines
"""

import logging
import asyncio


# ---------------------------------------------------------
# Faction registry (loaded from world-packs later)
# ---------------------------------------------------------

FACTIONS = {
    "crystalwood": {
        "name": "Crystalwood Wardens",
        "desc": "Guardians of the ancient Crystalwood Glade.",
        "ranks": [
            ("Outsider", 0),
            ("Friend", 100),
            ("Warden", 250),
            ("Sentinel", 500),
            ("Heartwood Keeper", 1000),
        ],
        "abilities": {
            "Warden": ["nature_sense"],
            "Sentinel": ["forest_step"],
            "Heartwood Keeper": ["glade_blessing"],
        },
        "shop": {
            "Friend": [6001, 6002],
            "Warden": [6003, 6004],
            "Sentinel": [6005],
            "Heartwood Keeper": [6006],
        },
        "quests": ["lost_relic"],
    },

    "obsidian_order": {
        "name": "Obsidian Order",
        "desc": "A secretive cabal of arcane scholars.",
        "ranks": [
            ("Uninitiated", 0),
            ("Acolyte", 150),
            ("Magister", 400),
            ("Shadowbinder", 800),
            ("Obsidian Archon", 1500),
        ],
        "abilities": {
            "Acolyte": ["arcane_focus"],
            "Magister": ["mana_flow"],
            "Shadowbinder": ["veil_step"],
            "Obsidian Archon": ["void_channel"],
        },
        "shop": {
            "Acolyte": [7001],
            "Magister": [7002, 7003],
            "Shadowbinder": [7004],
            "Obsidian Archon": [7005],
        },
        "quests": ["obsidian_trial"],
    }
}

# ---------------------------------------------------------
# Player faction state
# ---------------------------------------------------------

def get_faction_rep(player, faction_id):
    return player.factions.get(faction_id, 0)


def add_faction_rep(player, faction_id, amount):
    current = player.factions.get(faction_id, 0)
    player.factions[faction_id] = current + amount
    return player.factions[faction_id]


def get_faction_rank(faction, rep):
    """Return rank name based on reputation."""
    ranks = faction["ranks"]
    best = ranks[0][0]
    for name, req in ranks:
        if rep >= req:
            best = name
    return best

# ---------------------------------------------------------
# FACTION LIST
# ---------------------------------------------------------

async def do_factions(player, args):
    """List all factions."""

    await player.send("\033[95mFactions of Cyrisea:\033[0m")

    for fid, faction in FACTIONS.items():
        await player.send(f"{faction['name']} — {faction['desc']}")


# ---------------------------------------------------------
# FACTION STATUS
# ---------------------------------------------------------

async def do_faction(player, args):
    """Show your standing with a faction."""

    if not args:
        await player.send("Faction which?")
        return

    fid = args.lower()
    if fid not in FACTIONS:
        await player.send("No such faction.")
        return

    faction = FACTIONS[fid]
    rep = get_faction_rep(player, fid)
    rank = get_faction_rank(faction, rep)

    await player.send(f"\033[94m{faction['name']}\033[0m")
    await player.send(f"Reputation: {rep}")
    await player.send(f"Rank: {rank}")

    # Show abilities unlocked
    abilities = faction["abilities"].get(rank, [])
    if abilities:
        await player.send("Abilities unlocked:")
        for a in abilities:
            await player.send(f" - {a}")

    # Show shop unlocks
    shop_items = faction["shop"].get(rank, [])
    if shop_items:
        await player.send("Shop items unlocked:")
        for vnum in shop_items:
            obj = player.world.objects.get(vnum)
            if obj:
                await player.send(f" - {obj.short_desc}")


# ---------------------------------------------------------
# FACTION SHOP
# ---------------------------------------------------------

async def do_fshop(player, args):
    """Open faction shop."""

    if not args:
        await player.send("Shop for which faction?")
        return

    fid = args.lower()
    if fid not in FACTIONS:
        await player.send("No such faction.")
        return

    faction = FACTIONS[fid]
    rep = get_faction_rep(player, fid)
    rank = get_faction_rank(faction, rep)

    items = faction["shop"].get(rank, [])
    if not items:
        await player.send("You have not unlocked any shop items.")
        return

    await player.send(f"\033[94m{faction['name']} Shop ({rank})\033[0m")

    for vnum in items:
        obj = player.world.objects.get(vnum)
        if obj:
            await player.send(f"{obj.short_desc} — {obj.value} gold")


# ---------------------------------------------------------
# FACTION ABILITIES
# ---------------------------------------------------------

async def do_fabilities(player, args):
    """Show all faction abilities you have unlocked."""

    await player.send("\033[95mFaction Abilities:\033[0m")

    for fid, faction in FACTIONS.items():
        rep = get_faction_rep(player, fid)
        rank = get_faction_rank(faction, rep)

        abilities = faction["abilities"].get(rank, [])
        if abilities:
            await player.send(f"{faction['name']} ({rank}):")
            for a in abilities:
                await player.send(f" - {a}")

COMMAND_DEFS = [
    ("factions",   do_factions,   {"position": "resting", "help_category": "factions"}),
    ("faction",    do_faction,    {"position": "resting", "help_category": "factions"}),
    ("fshop",      do_fshop,      {"position": "standing", "help_category": "factions"}),
    ("fabilities", do_fabilities, {"position": "resting", "help_category": "factions"}),
]
