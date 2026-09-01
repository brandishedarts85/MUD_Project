"""
Realms of Cyrisea - Reputation System
Full reputation suite:
- Global reputation
- Regional reputation
- NPC reputation
- Reputation shops
- Reputation dialogue
- Reputation decay
- Reputation categories
- Reputation achievements
"""

import asyncio
import logging
import random

# ---------------------------------------------------------
# Reputation categories
# ---------------------------------------------------------

REPUTATION_CATEGORIES = {
    "global": "Global Reputation",
    "regional": "Regional Reputation",
    "npc": "NPC Reputation",
    "faction": "Faction Reputation",
    "guild": "Guild Reputation",
}

# ---------------------------------------------------------
# Reputation thresholds
# ---------------------------------------------------------

REPUTATION_TIERS = [
    ("Hated", -1000),
    ("Hostile", -500),
    ("Unfriendly", -100),
    ("Neutral", 0),
    ("Friendly", 250),
    ("Honored", 500),
    ("Revered", 750),
    ("Exalted", 1000),
]

# ---------------------------------------------------------
# Player reputation state
# ---------------------------------------------------------

def get_rep_tier(value):
    tier = "Neutral"
    for name, threshold in REPUTATION_TIERS:
        if value >= threshold:
            tier = name
    return tier

def get_reputation(player, category, key):
    return player.reputation.get(category, {}).get(key, 0)

def modify_reputation(player, category, key, amount):
    player.reputation.setdefault(category, {})
    player.reputation[category][key] = player.reputation[category].get(key, 0) + amount
    return player.reputation[category][key]

# ---------------------------------------------------------
# Reputation decay
# ---------------------------------------------------------

async def reputation_tick(world):
    """Slow decay of reputation over time."""

    for p in world.players:
        for cat, entries in p.reputation.items():
            for key, value in entries.items():
                if value > 0:
                    p.reputation[cat][key] -= 1
                elif value < 0:
                    p.reputation[cat][key] += 1

# ---------------------------------------------------------
# Reputation shops
# ---------------------------------------------------------

async def do_repshop(player, args):
    """Open a reputation-based shop."""

    shop = getattr(player.room, "reputation_shop", None)
    if not shop:
        await player.send("There is no reputation shop here.")
        return

    category = shop["category"]
    key = shop["key"]

    rep = get_reputation(player, category, key)
    tier = get_rep_tier(rep)

    await player.send(f"\033[94mReputation Shop ({tier})\033[0m")

    for entry in shop["items"]:
        item = player.world.objects.get(entry["vnum"])
        if not item:
            continue

        required = entry["required_rep"]
        if rep >= required:
            price = entry["price"]
            await player.send(f"{item.short_desc} — {price} gold (requires {required} rep)")
        else:
            await player.send(f"{item.short_desc} — LOCKED (requires {required} rep)")

# ---------------------------------------------------------
# Reputation dialogue
# ---------------------------------------------------------

async def do_repdialogue(player, args):
    """Speak with an NPC using reputation-based dialogue."""

    npc = player.room.find_npc(args)
    if not npc:
        await player.send("They aren't here.")
        return

    rep = get_reputation(player, "npc", npc.name.lower())
    tier = get_rep_tier(rep)

    dialogue = npc.dialogue.get(tier, npc.dialogue.get("Neutral", "They have nothing to say."))

    await player.send(f"{npc.name} says: \"{dialogue}\"")

# ---------------------------------------------------------
# Reputation gains from actions
# ---------------------------------------------------------

async def rep_gain_kill(player, mob):
    """Gain or lose reputation from killing mobs."""

    if mob.rep_gain:
        for cat, key, amt in mob.rep_gain:
            new_val = modify_reputation(player, cat, key, amt)
            await player.send(f"Reputation with {key} changed by {amt} (now {new_val}).")

async def rep_gain_collect(player, obj):
    """Gain reputation from collecting items."""

    if obj.rep_gain:
        for cat, key, amt in obj.rep_gain:
            new_val = modify_reputation(player, cat, key, amt)
            await player.send(f"Reputation with {key} changed by {amt} (now {new_val}).")

# ---------------------------------------------------------
# Reputation achievements
# ---------------------------------------------------------

async def check_reputation_achievements(player):
    for cat, entries in player.reputation.items():
        for key, value in entries.items():
            tier = get_rep_tier(value)
            if tier == "Exalted":
                await player.send(f"\033[95mAchievement Unlocked:\033[0m Exalted with {key}")

async def do_reputation(player, args):
    """View your reputation."""

    await player.send("\033[95mReputation Overview:\033[0m")

    for cat, entries in player.reputation.items():
        await player.send(f"{REPUTATION_CATEGORIES.get(cat, cat.title())}:")
        for key, value in entries.items():
            tier = get_rep_tier(value)
            await player.send(f" - {key.title()}: {value} ({tier})")

async def do_repmod(player, args):
    """Admin: modify reputation."""

    if not player.is_admin:
        await player.send("You do not have permission.")
        return

    parts = args.split()
    if len(parts) != 3:
        await player.send("Syntax: repmod <category> <key> <amount>")
        return

    cat, key, amt = parts
    amt = int(amt)

    new_val = modify_reputation(player, cat, key, amt)
    await player.send(f"Reputation with {key} is now {new_val}.")

COMMAND_DEFS = [
    ("reputation",   do_reputation,   {"position": "standing", "help_category": "reputation"}),
    ("repshop",      do_repshop,      {"position": "standing", "help_category": "reputation"}),
    ("repdialogue",  do_repdialogue,  {"position": "standing", "help_category": "reputation"}),
    ("repmod",       do_repmod,       {"position": "standing", "help_category": "reputation"}),
]
