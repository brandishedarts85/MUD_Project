"""
Realms of Cyrisea - Combat System
Full combat suite:
- Damage types
- Resistances
- Crits, dodging, blocking
- Skills & spells
- Combat rounds
- Status effects
- Elemental interactions
- Weather & event modifiers
- PvP integration (peaceful/deadly, hostility, corpse/death system)
"""

import asyncio
import random
import logging

# NEW IMPORTS FOR PVP + DEATH + CORPSES
from commands.pvp import (
    pvp_attack_check,
    handle_player_death,
)

log = logging.getLogger(__name__)


# ---------------------------------------------------------
# Damage types
# ---------------------------------------------------------

DAMAGE_TYPES = [
    "physical",
    "fire",
    "ice",
    "lightning",
    "poison",
    "arcane",
]


# ---------------------------------------------------------
# Status effects
# ---------------------------------------------------------

STATUS_EFFECTS = {
    "burn": {
        "desc": "You are burning!",
        "tick_damage": 5,
        "duration": 5,
    },
    "freeze": {
        "desc": "You are frozen!",
        "movement_mod": 0.5,
        "duration": 3,
    },
    "shock": {
        "desc": "Lightning disrupts your focus!",
        "mana_mod": 0.8,
        "duration": 4,
    },
    "poison": {
        "desc": "Poison courses through your veins!",
        "tick_damage": 3,
        "duration": 8,
    },
}


# ---------------------------------------------------------
# Combat modifiers from weather & events
# ---------------------------------------------------------

def get_combat_modifiers(player):
    """Return combined combat modifiers from weather, events, and faction abilities."""

    world = player.world
    room = player.room

    mod = {
        "damage": 1.0,
        "defense": 1.0,
        "crit": 1.0,
        "dodge": 1.0,
    }

    # Weather
    region = getattr(room, "region", None)
    if region:
        weather = world.weather.get(region, {})
        wtype = weather.get("type")
        if wtype:
            effect = world.weather_effects.get(wtype, {})
            mod["damage"] *= effect.get("combat_mod", 1.0)

    # Events
    for eid, data in world.active_events.items():
        event = data["data"]
        if event["region"] == region:
            effect = event.get("effects", {})
            mod["damage"] *= effect.get("combat_mod", 1.0)

    # Faction abilities
    for fid, rep in player.factions.items():
        faction = world.factions.get(fid)
        if not faction:
            continue
        rank = world.get_faction_rank(faction, rep)
        abilities = faction["abilities"].get(rank, [])
        if "forest_step" in abilities and room.sector == "forest":
            mod["dodge"] *= 1.2
        if "glade_blessing" in abilities and region == "crystalwood":
            mod["damage"] *= 1.15

    return mod


# ---------------------------------------------------------
# Core combat roll functions
# ---------------------------------------------------------

def roll_hit(attacker, defender):
    """Determine if an attack hits."""

    base = 75  # base hit chance
    dodge = defender.stats.get("dodge", 0)

    # Combat modifiers
    mods = get_combat_modifiers(defender)
    dodge *= mods["dodge"]

    chance = base - dodge
    return random.randint(1, 100) <= chance


def roll_crit(attacker):
    """Determine if attack crits."""
    crit = attacker.stats.get("crit", 5)
    mods = get_combat_modifiers(attacker)
    crit *= mods["crit"]
    return random.randint(1, 100) <= crit


def roll_block(defender):
    """Determine if defender blocks."""
    block = defender.stats.get("block", 0)
    return random.randint(1, 100) <= block


# ---------------------------------------------------------
# Damage calculation
# ---------------------------------------------------------

def calculate_damage(attacker, defender, dtype):
    """Calculate damage with resistances and modifiers."""

    base = attacker.stats.get("attack", 10)

    # Damage type scaling
    if dtype == "fire":
        base *= 1.1
    elif dtype == "ice":
        base *= 1.05
    elif dtype == "lightning":
        base *= 1.15
    elif dtype == "poison":
        base *= 0.8
    elif dtype == "arcane":
        base *= 1.2

    # Resistances
    resist = defender.resistances.get(dtype, 0)
    base *= (1 - resist)

    # Combat modifiers
    mods = get_combat_modifiers(attacker)
    base *= mods["damage"]

    return int(base)


# ---------------------------------------------------------
# Apply status effects
# ---------------------------------------------------------

async def apply_status(attacker, defender, dtype):
    """Apply status effects based on damage type."""

    if dtype == "fire" and random.random() < 0.2:
        defender.add_status("burn")
    elif dtype == "ice" and random.random() < 0.15:
        defender.add_status("freeze")
    elif dtype == "lightning" and random.random() < 0.15:
        defender.add_status("shock")
    elif dtype == "poison" and random.random() < 0.25:
        defender.add_status("poison")


# ---------------------------------------------------------
# Combat round
# ---------------------------------------------------------

async def combat_round(attacker, defender):
    """Execute a single combat round."""

    if not roll_hit(attacker, defender):
        await attacker.send("You miss!")
        await defender.send(f"{attacker.name} misses you.")
        return

    if roll_block(defender):
        await attacker.send("Your attack is blocked!")
        await defender.send(f"You block {attacker.name}'s attack.")
        return

    dtype = attacker.stats.get("damage_type", "physical")
    dmg = calculate_damage(attacker, defender, dtype)

    if roll_crit(attacker):
        dmg = int(dmg * 1.5)
        await attacker.send("Critical hit!")
        await defender.send("You are critically struck!")

    defender.hp -= dmg

    await attacker.send(f"You hit {defender.name} for {dmg} damage.")
    await defender.send(f"{attacker.name} hits you for {dmg} damage.")

    await apply_status(attacker, defender, dtype)

    if defender.hp <= 0:
        # NEW: Player death goes through PvP/death system
        if hasattr(defender, "is_peaceful"):
            await handle_player_death(attacker.world, defender)
        else:
            await kill_target(attacker, defender)


# ---------------------------------------------------------
# Kill target (Mob only)
# ---------------------------------------------------------

async def kill_target(attacker, defender):
    """Handle mob death."""

    await attacker.send(f"You have slain {defender.name}!")
    await defender.send("You have been slain.")

    defender.hp = defender.max_hp
    respawn = defender.respawn_point or attacker.world.default_respawn

    await defender.room.leave(defender)
    await respawn.enter(defender)

    await defender.send("You awaken at a safe location.")


# ---------------------------------------------------------
# Player attack command
# ---------------------------------------------------------

async def do_attack(player, args):
    """Attack a mob or player."""

    if not args:
        await player.send("Attack whom.")
        return

    target = player.room.find_mob(args) or player.room.find_player(args)

    if not target:
        await player.send("They aren't here.")
        return

    if target == player:
        await player.send("You cannot attack yourself.")
        return

    # NEW: PvP rules check BEFORE elemental combat
    allowed = await pvp_attack_check(player, target, player.world)
    if not allowed:
        return

    player.fighting = target
    target.fighting = player

    await player.send(f"You engage {target.name} in combat!")
    await target.send(f"{player.name} attacks you!")

    # Combat loop
    while player.fighting == target and target.hp > 0 and player.hp > 0:
        await combat_round(player, target)
        if target.hp > 0:
            await combat_round(target, player)
        await asyncio.sleep(2)

    player.fighting = None
    target.fighting = None


# ---------------------------------------------------------
# Command definitions
# ---------------------------------------------------------

COMMAND_DEFS = [
    ("attack", do_attack, {"position": "standing", "help_category": "combat"}),
]
