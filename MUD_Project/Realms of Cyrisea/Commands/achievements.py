"""
Realms of Cyrisea - Achievement System
Full achievement suite:
- Achievement categories
- Hidden achievements
- Milestone achievements
- Account-wide achievements
- Achievement points
- Achievement rewards
"""

import asyncio
import logging
import random

# ---------------------------------------------------------
# Achievement categories
# ---------------------------------------------------------

ACHIEVEMENT_CATEGORIES = {
    "combat": "Combat Achievements",
    "exploration": "Exploration Achievements",
    "crafting": "Crafting Achievements",
    "faction": "Faction Achievements",
    "guild": "Guild Achievements",
    "pets": "Pet Achievements",
    "housing": "Housing Achievements",
    "events": "Event Achievements",
    "quests": "Quest Achievements",
    "economy": "Economy Achievements",
    "hidden": "Hidden Achievements",
}

# ---------------------------------------------------------
# Achievement registry
# ---------------------------------------------------------

ACHIEVEMENTS = {
    # Combat
    "first_blood": {
        "name": "First Blood",
        "category": "combat",
        "desc": "Defeat your first enemy.",
        "points": 10,
        "trigger": {"type": "kill_count", "count": 1},
    },
    "slayer_100": {
        "name": "Hundred Slayer",
        "category": "combat",
        "desc": "Defeat 100 enemies.",
        "points": 50,
        "trigger": {"type": "kill_count", "count": 100},
    },

    # Exploration
    "worldwalker": {
        "name": "Worldwalker",
        "category": "exploration",
        "desc": "Visit 50 unique rooms.",
        "points": 40,
        "trigger": {"type": "rooms_visited", "count": 50},
    },
    "crystalwood_cartographer": {
        "name": "Crystalwood Cartographer",
        "category": "exploration",
        "desc": "Fully explore Crystalwood.",
        "points": 60,
        "trigger": {"type": "region_explore", "region": "crystalwood"},
    },

    # Crafting
    "apprentice_crafter": {
        "name": "Apprentice Crafter",
        "category": "crafting",
        "desc": "Craft 10 items.",
        "points": 20,
        "trigger": {"type": "craft_count", "count": 10},
    },
    "master_enchanter": {
        "name": "Master Enchanter",
        "category": "crafting",
        "desc": "Perform 20 enchantments.",
        "points": 50,
        "trigger": {"type": "enchant_count", "count": 20},
    },

    # Faction
    "crystalwood_loyalist": {
        "name": "Crystalwood Loyalist",
        "category": "faction",
        "desc": "Reach Warden rank with Crystalwood.",
        "points": 30,
        "trigger": {"type": "faction_rank", "faction": "crystalwood", "rank": "Warden"},
    },

    # Guild
    "guild_founder": {
        "name": "Guild Founder",
        "category": "guild",
        "desc": "Create a guild.",
        "points": 50,
        "trigger": {"type": "guild_create"},
    },
    "guild_officer": {
        "name": "Guild Officer",
        "category": "guild",
        "desc": "Reach Officer rank.",
        "points": 40,
        "trigger": {"type": "guild_rank", "rank": "Officer"},
    },

    # Pets
    "pet_parent": {
        "name": "Pet Parent",
        "category": "pets",
        "desc": "Acquire your first pet.",
        "points": 10,
        "trigger": {"type": "pet_acquired"},
    },
    "pet_trainer": {
        "name": "Pet Trainer",
        "category": "pets",
        "desc": "Level a pet to level 10.",
        "points": 50,
        "trigger": {"type": "pet_level", "level": 10},
    },

    # Housing
    "homeowner": {
        "name": "Homeowner",
        "category": "housing",
        "desc": "Purchase a home.",
        "points": 20,
        "trigger": {"type": "home_purchase"},
    },
    "master_gardener": {
        "name": "Master Gardener",
        "category": "housing",
        "desc": "Harvest 20 plants.",
        "points": 40,
        "trigger": {"type": "harvest_count", "count": 20},
    },

    # Events
    "event_defender": {
        "name": "Event Defender",
        "category": "events",
        "desc": "Complete an invasion event.",
        "points": 30,
        "trigger": {"type": "event_complete", "event": "forest_invasion"},
    },

    # Quests
    "storyteller": {
        "name": "Storyteller",
        "category": "quests",
        "desc": "Complete 20 quests.",
        "points": 50,
        "trigger": {"type": "quest_count", "count": 20},
    },

    # Economy
    "merchant": {
        "name": "Merchant",
        "category": "economy",
        "desc": "Buy or sell 50 items.",
        "points": 30,
        "trigger": {"type": "trade_count", "count": 50},
    },

    # Hidden
    "secret_keeper": {
        "name": "Secret Keeper",
        "category": "hidden",
        "desc": "Discover a hidden room.",
        "points": 100,
        "trigger": {"type": "discover_secret"},
        "hidden": True,
    },
}

# ---------------------------------------------------------
# Player achievement state
# ---------------------------------------------------------

def get_achievements(player):
    return player.achievements

def award_achievement(player, ach_id):
    if ach_id in player.achievements:
        return False

    player.achievements.add(ach_id)
    player.achievement_points += ACHIEVEMENTS[ach_id]["points"]
    return True

# ---------------------------------------------------------
# Achievement trigger system
# ---------------------------------------------------------

async def check_achievements(player, trigger_type, value=None):
    for ach_id, ach in ACHIEVEMENTS.items():
        trig = ach["trigger"]

        if trig["type"] != trigger_type:
            continue

        # Match trigger conditions
        if trigger_type == "kill_count":
            if player.kill_count >= trig["count"]:
                await grant_achievement(player, ach_id)

        elif trigger_type == "rooms_visited":
            if len(player.rooms_visited) >= trig["count"]:
                await grant_achievement(player, ach_id)

        elif trigger_type == "region_explore":
            if trig["region"] in player.regions_explored:
                await grant_achievement(player, ach_id)

        elif trigger_type == "craft_count":
            if player.craft_count >= trig["count"]:
                await grant_achievement(player, ach_id)

        elif trigger_type == "enchant_count":
            if player.enchant_count >= trig["count"]:
                await grant_achievement(player, ach_id)

        elif trigger_type == "faction_rank":
            fid = trig["faction"]
            rank = trig["rank"]
            if player.factions.get(fid, 0) >= player.world.get_faction_rank_value(fid, rank):
                await grant_achievement(player, ach_id)

        elif trigger_type == "guild_create":
            if player.guild and player.guild_rank == "Leader":
                await grant_achievement(player, ach_id)

        elif trigger_type == "guild_rank":
            if player.guild_rank == trig["rank"]:
                await grant_achievement(player, ach_id)

        elif trigger_type == "pet_acquired":
            if player.pet_data:
                await grant_achievement(player, ach_id)

        elif trigger_type == "pet_level":
            if player.pet_data and player.pet_data["level"] >= trig["level"]:
                await grant_achievement(player, ach_id)

        elif trigger_type == "home_purchase":
            if player.home:
                await grant_achievement(player, ach_id)

        elif trigger_type == "harvest_count":
            if player.harvest_count >= trig["count"]:
                await grant_achievement(player, ach_id)

        elif trigger_type == "event_complete":
            if value == trig["event"]:
                await grant_achievement(player, ach_id)

        elif trigger_type == "quest_count":
            if player.quest_complete_count >= trig["count"]:
                await grant_achievement(player, ach_id)

        elif trigger_type == "trade_count":
            if player.trade_count >= trig["count"]:
                await grant_achievement(player, ach_id)

        elif trigger_type == "discover_secret":
            if value == "secret_room":
                await grant_achievement(player, ach_id)

# ---------------------------------------------------------
# Grant achievement
# ---------------------------------------------------------

async def grant_achievement(player, ach_id):
    if not award_achievement(player, ach_id):
        return

    ach = ACHIEVEMENTS[ach_id]

    # Hidden achievements reveal only when earned
    if ach.get("hidden"):
        await player.send("\033[95mHidden Achievement Unlocked!\033[0m")
    else:
        await player.send("\033[94mAchievement Unlocked!\033[0m")

    await player.send(f"{ach['name']} — {ach['desc']}")
    await player.send(f"Achievement Points: +{ach['points']}")

async def do_achievements(player, args):
    """List achievements."""

    if not player.achievements:
        await player.send("You have not unlocked any achievements.")
        return

    await player.send("\033[95mAchievements:\033[0m")
    for ach_id in player.achievements:
        ach = ACHIEVEMENTS[ach_id]
        await player.send(f"{ach['name']} — {ach['desc']} ({ach['points']} pts)")

async def do_achcat(player, args):
    """List achievement categories."""

    await player.send("\033[94mAchievement Categories:\033[0m")
    for cid, cname in ACHIEVEMENT_CATEGORIES.items():
        await player.send(f" - {cname}")

async def do_ach(player, args):
    """Show achievement details."""

    if not args:
        await player.send("Achievement which?")
        return

    ach_id = args.lower()
    if ach_id not in ACHIEVEMENTS:
        await player.send("No such achievement.")
        return

    ach = ACHIEVEMENTS[ach_id]

    await player.send(f"\033[94m{ach['name']}\033[0m")
    await player.send(ach["desc"])
    await player.send(f"Category: {ACHIEVEMENT_CATEGORIES[ach['category']]}")
    await player.send(f"Points: {ach['points']}")

COMMAND_DEFS = [
    ("achievements", do_achievements, {"position": "standing", "help_category": "achievements"}),
    ("achcat",       do_achcat,       {"position": "standing", "help_category": "achievements"}),
    ("ach",          do_ach,          {"position": "standing", "help_category": "achievements"}),
]
