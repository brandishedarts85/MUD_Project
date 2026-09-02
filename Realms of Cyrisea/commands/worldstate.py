"""
Realms of Cyrisea - World State System
Full world state suite:
- Global world variables
- Regional world states
- Persistent world changes
- Player-driven world changes
- Event-driven world changes
- Faction war states
- Environmental world states
- World state triggers
"""

import asyncio
import logging
import random

# ---------------------------------------------------------
# World state structure
# ---------------------------------------------------------

DEFAULT_WORLD_STATE = {
    "global": {
        "day": 1,
        "season": "spring",
        "magic_level": 100,
        "world_tension": 0,
        "faction_war": None,
    },

    "regions": {
        "crystalwood": {
            "purity": 100,
            "shadow_influence": 0,
            "weather_bias": "clear",
            "event_history": [],
        },
        "obsidian_order": {
            "arcane_flux": 50,
            "storm_activity": 20,
            "event_history": [],
        },
        "sunspire": {
            "trade_health": 100,
            "pirate_threat": 0,
            "event_history": [],
        },
        "frostpeak": {
            "blizzard_strength": 30,
            "frozen_corruption": 0,
            "event_history": [],
        },
    },

    "environment": {
        "magic_storms": False,
        "shadow_rifts": [],
        "arcane_nodes": [],
    },
}

# ---------------------------------------------------------
# Initialize world state
# ---------------------------------------------------------

def init_world_state(world):
    world.state = DEFAULT_WORLD_STATE.copy()

# ---------------------------------------------------------
# Global world modifiers
# ---------------------------------------------------------

def modify_global(world, key, amount):
    world.state["global"][key] += amount
    return world.state["global"][key]

def set_global(world, key, value):
    world.state["global"][key] = value

# ---------------------------------------------------------
# Regional world modifiers
# ---------------------------------------------------------

def modify_region(world, region, key, amount):
    world.state["regions"][region][key] += amount
    return world.state["regions"][region][key]

def set_region(world, region, key, value):
    world.state["regions"][region][key] = value

# ---------------------------------------------------------
# Environmental world modifiers
# ---------------------------------------------------------

def add_shadow_rift(world, room_vnum):
    world.state["environment"]["shadow_rifts"].append(room_vnum)

def close_shadow_rift(world, room_vnum):
    if room_vnum in world.state["environment"]["shadow_rifts"]:
        world.state["environment"]["shadow_rifts"].remove(room_vnum)

def add_arcane_node(world, room_vnum):
    world.state["environment"]["arcane_nodes"].append(room_vnum)

# ---------------------------------------------------------
# World tick (daily)
# ---------------------------------------------------------

async def world_tick(world):
    """Daily world update."""

    # Advance day
    world.state["global"]["day"] += 1

    # Seasonal cycle
    day = world.state["global"]["day"]
    if day % 30 == 0:
        cycle_season(world)

    # Natural decay
    for region, data in world.state["regions"].items():
        if "shadow_influence" in data:
            data["shadow_influence"] = max(0, data["shadow_influence"] - 1)
        if "pirate_threat" in data:
            data["pirate_threat"] = max(0, data["pirate_threat"] - 1)
        if "frozen_corruption" in data:
            data["frozen_corruption"] = max(0, data["frozen_corruption"] - 1)

    # Environmental events
    if random.random() < 0.05:
        await spawn_magic_storm(world)

    if random.random() < 0.03:
        await spawn_shadow_rift(world)

# ---------------------------------------------------------
# Seasonal cycle
# ---------------------------------------------------------

def cycle_season(world):
    seasons = ["spring", "summer", "autumn", "winter"]
    current = world.state["global"]["season"]
    idx = seasons.index(current)
    new_season = seasons[(idx + 1) % 4]
    world.state["global"]["season"] = new_season

# ---------------------------------------------------------
# Magic storms
# ---------------------------------------------------------

async def spawn_magic_storm(world):
    world.state["environment"]["magic_storms"] = True

    for p in world.players:
        await p.send("\033[95mA surge of arcane energy sweeps across Cyrisea!\033[0m")

    # Boost arcane spells temporarily
    world.global_spell_mod = 1.2

async def end_magic_storm(world):
    world.state["environment"]["magic_storms"] = False
    world.global_spell_mod = 1.0

# ---------------------------------------------------------
# Shadow rifts
# ---------------------------------------------------------

async def spawn_shadow_rift(world):
    room = random.choice(list(world.rooms.values()))
    add_shadow_rift(world, room.vnum)

    for p in world.players:
        await p.send("\033[90mA shadow rift tears open somewhere in Cyrisea...\033[0m")

# ---------------------------------------------------------
# Faction war states
# ---------------------------------------------------------

def start_faction_war(world, faction1, faction2):
    world.state["global"]["faction_war"] = (faction1, faction2)

def end_faction_war(world):
    world.state["global"]["faction_war"] = None

# ---------------------------------------------------------
# Player-driven world changes
# ---------------------------------------------------------

async def player_action_change(world, player, action):
    """Player actions that affect world state."""

    if action == "purify_crystalwood":
        modify_region(world, "crystalwood", "purity", 5)
        modify_region(world, "crystalwood", "shadow_influence", -5)
        await player.send("The Heartwood glows brighter.")

    if action == "strengthen_obsidian_flux":
        modify_region(world, "obsidian_order", "arcane_flux", 10)
        await player.send("Arcane energy surges through the Obsidian Highlands.")

    if action == "defend_sunspire":
        modify_region(world, "sunspire", "pirate_threat", -10)
        await player.send("Sunspire’s trade routes grow safer.")

    if action == "cleanse_frostpeak":
        modify_region(world, "frostpeak", "frozen_corruption", -10)
        await player.send("The icy winds soften slightly.")

# ---------------------------------------------------------
# Event-driven world changes
# ---------------------------------------------------------

async def apply_event_world_changes(world, event_id):
    event = world.active_events[event_id]["data"]
    region = event["region"]

    # Invasion increases shadow influence
    if event["type"] == "invasion":
        modify_region(world, region, "shadow_influence", 20)

    # Festival increases trade health or arcane flux
    if event["type"] == "festival":
        if region == "sunspire":
            modify_region(world, region, "trade_health", 10)
        if region == "obsidian_order":
            modify_region(world, region, "arcane_flux", 10)

    # Seasonal storms increase blizzard strength
    if event["type"] == "seasonal":
        if region == "frostpeak":
            modify_region(world, region, "blizzard_strength", 15)

    # World boss increases world tension
    if event["type"] == "world_boss":
        modify_global(world, "world_tension", 20)

# ---------------------------------------------------------
# World state triggers
# ---------------------------------------------------------

async def check_world_triggers(world):
    """Check for major world state thresholds."""

    # Shadow corruption
    if world.state["regions"]["crystalwood"]["shadow_influence"] >= 100:
        await trigger_shadow_overgrowth(world)

    # Arcane overload
    if world.state["regions"]["obsidian_order"]["arcane_flux"] >= 200:
        await trigger_arcane_overload(world)

    # Trade collapse
    if world.state["regions"]["sunspire"]["trade_health"] <= 0:
        await trigger_trade_collapse(world)

    # Frozen cataclysm
    if world.state["regions"]["frostpeak"]["frozen_corruption"] >= 100:
        await trigger_frozen_cataclysm(world)

# ---------------------------------------------------------
# Major world events
# ---------------------------------------------------------

async def trigger_shadow_overgrowth(world):
    for p in world.players:
        await p.send("\033[90mShadow vines choke Crystalwood! The region is corrupted.\033[0m")
    world.state["regions"]["crystalwood"]["weather_bias"] = "fog"

async def trigger_arcane_overload(world):
    for p in world.players:
        await p.send("\033[95mArcane storms erupt across the Obsidian Highlands!\033[0m")
    world.state["environment"]["magic_storms"] = True

async def trigger_trade_collapse(world):
    for p in world.players:
        await p.send("\033[93mSunspire’s trade routes collapse! Prices skyrocket.\033[0m")
    world.state["regions"]["sunspire"]["pirate_threat"] = 100

async def trigger_frozen_cataclysm(world):
    for p in world.players:
        await p.send("\033[96mFrostpeak is consumed by frozen corruption!\033[0m")
    world.state["regions"]["frostpeak"]["blizzard_strength"] = 100

async def do_worldstate(player, args):
    """View the current world state."""

    ws = player.world.state

    await player.send("\033[95mGlobal World State:\033[0m")
    for k, v in ws["global"].items():
        await player.send(f" - {k.title()}: {v}")

    await player.send("\033[94mRegional States:\033[0m")
    for region, data in ws["regions"].items():
        await player.send(f"{region.title()}:")
        for k, v in data.items():
            await player.send(f"   - {k}: {v}")

    await player.send("\033[96mEnvironmental States:\033[0m")
    for k, v in ws["environment"].items():
        await player.send(f" - {k}: {v}")

async def do_worldmod(player, args):
    """Admin: modify world state."""

    if not player.is_admin:
        await player.send("You do not have permission.")
        return

    parts = args.split()
    if len(parts) != 3:
        await player.send("Syntax: worldmod <region/global> <key> <amount>")
        return

    scope, key, amt = parts
    amt = int(amt)

    if scope == "global":
        new_val = modify_global(player.world, key, amt)
        await player.send(f"Global {key} is now {new_val}.")
        return

    if scope in player.world.state["regions"]:
        new_val = modify_region(player.world, scope, key, amt)
        await player.send(f"{scope.title()} {key} is now {new_val}.")
        return

    await player.send("Invalid scope.")

COMMAND_DEFS = [
    ("worldstate", do_worldstate, {"position": "standing", "help_category": "world"}),
    ("worldmod",   do_worldmod,   {"position": "standing", "help_category": "world"}),
]
