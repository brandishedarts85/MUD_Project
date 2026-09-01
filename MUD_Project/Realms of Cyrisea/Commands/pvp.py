"""
Realms of Cyrisea - PvP, Death, and Corpse System
Handles:
- Peaceful vs Deadly mode
- Temporary hostility
- PvP level-range fairness
- Player death
- Corpse creation
- Corpse decay
- Resurrection
- Corpse retrieval
- Corpse summoning (deity/NPC)
"""

import asyncio
import time
from core import Corpse


# ---------------------------------------------------------
# PvP Level Range Fairness
# ---------------------------------------------------------

def within_pvp_range(attacker, target):
    """Deadly players can only attack within ±5 levels."""
    a_lvl = attacker.stats.get("level", 1)
    t_lvl = target.stats.get("level", 1)
    return abs(a_lvl - t_lvl) <= 5


# ---------------------------------------------------------
# Attack Entry Point (PvP Gate)
# ---------------------------------------------------------

async def pvp_attack_check(attacker, target, world):
    """
    This function is called BEFORE the elemental combat engine.
    It determines whether the attack is allowed under PvP rules.
    """

    # -------------------------
    # PvP: Player attacking Player
    # -------------------------
    if hasattr(target, "is_peaceful"):

        # Peaceful vs Peaceful
        if attacker.is_peaceful and target.is_peaceful:
            await attacker.send("You cannot attack another peaceful player.")
            return False

        # Peaceful attacking Deadly → temporary hostility
        if attacker.is_peaceful and target.is_deadly:
            await attacker.send(
                "You are peaceful. Attacking a deadly player will make you "
                "temporarily hostile for 5 minutes or until death. Proceed (yes/no)."
            )
            confirm = (await world.input(attacker)).strip().lower()
            if confirm != "yes":
                await attacker.send("You decide against attacking.")
                return False

            attacker.is_hostile = True
            attacker.hostile_until = world.now() + 5 * 60
            await attacker.send("You are now temporarily hostile.")

        # Deadly vs Deadly → check level range
        if attacker.is_deadly and target.is_deadly:
            if not within_pvp_range(attacker, target):
                await attacker.send("They are too far outside your level range.")
                return False

        # PvP allowed
        return True

    # -------------------------
    # PvE: Player attacking Mob
    # -------------------------
    return True


# ---------------------------------------------------------
# Death Handling
# ---------------------------------------------------------

async def handle_player_death(world, player):
    """Handles player death, corpse creation, and resurrection."""

    now = world.now()

    # Determine corpse decay time
    decay_seconds = 5 * 60 if player.is_deadly else 10 * 60
    decay_time = now + decay_seconds

    # Determine what items go into corpse
    items_for_corpse = []
    gold_for_corpse = player.gold

    if player.is_deadly:
        # deadly: all inventory is at risk
        items_for_corpse = list(player.inventory)
    else:
        # peaceful: only non-equipped items
        items_for_corpse = [
            i for i in player.inventory if not getattr(i, "equipped", False)
        ]

    # Create corpse
    corpse = Corpse(
        owner_name=player.name,
        room=player.room,
        items=items_for_corpse,
        gold=gold_for_corpse,
        decay_time=decay_time,
        is_deadly=player.is_deadly,
        world=world
    )

    world.corpses.append(corpse)
    player.last_corpse = corpse
    player.last_death_time = now

    # Remove items/gold from player
    player.inventory = [i for i in player.inventory if i not in items_for_corpse]
    player.gold = 0

    # Clear temporary hostility
    player.is_hostile = False
    player.hostile_until = None

    # Apply death penalties
    if player.is_deadly:
        player.durability_penalty += 2
        player.fatigue += 20
    else:
        player.durability_penalty += 1
        player.fatigue += 10

    # Respawn player
    await resurrect_player(world, player)


# ---------------------------------------------------------
# Resurrection
# ---------------------------------------------------------

async def resurrect_player(world, player):
    """Move player to a resurrection room."""
    if world.rooms:
        res_room = next(iter(world.rooms.values()))
        await res_room.enter(player)
        await player.send("You have been resurrected.")
    else:
        await player.send("Error: No resurrection rooms exist.")


# ---------------------------------------------------------
# Corpse Retrieval
# ---------------------------------------------------------

async def cmd_getcorpse(player, args):
    world = player.world
    corpse = player.last_corpse

    if not corpse or corpse.decayed:
        await player.send("Your corpse has already decayed or does not exist.")
        return

    if player.room != corpse.room:
        await player.send("You are not at your corpse.")
        return

    # Transfer items/gold back
    player.inventory.extend(corpse.items)
    player.gold += corpse.gold

    corpse.items.clear()
    corpse.gold = 0
    corpse.decayed = True
    world.corpses.remove(corpse)

    await player.send("You recover your corpse and belongings.")


# ---------------------------------------------------------
# Corpse Summoning (Deity/NPC)
# ---------------------------------------------------------

async def cmd_summoncorpse(player, args):
    world = player.world
    corpse = player.last_corpse

    if not corpse or corpse.decayed:
        await player.send("Your corpse has already decayed or does not exist.")
        return

    # Cost calculation
    if player.is_deadly:
        exp_cost = int(player.exp * 0.10)
        favor_cost = 25
    else:
        exp_cost = int(player.exp * 0.05)
        favor_cost = 10

    if player.exp < exp_cost or player.favor < favor_cost:
        await player.send("You lack the experience or favor to perform this ritual.")
        return

    # Pay costs
    player.exp -= exp_cost
    player.favor -= favor_cost

    # Move corpse to player’s current room
    corpse.room = player.room
    await player.send("Your deity answers. Your corpse is drawn to your side.")


# ---------------------------------------------------------
# Hostility Timer Processing
# ---------------------------------------------------------

async def process_hostility(world):
    now = world.now()
    for player in world.players:
        if player.is_hostile and player.hostile_until and now >= player.hostile_until:
            player.is_hostile = False
            player.hostile_until = None
            await player.send("Your hostility fades. You are no longer attackable.")


# ---------------------------------------------------------
# Corpse Decay Processing
# ---------------------------------------------------------

async def process_corpses(world):
    now = world.now()
    for corpse in list(world.corpses):
        if corpse.should_decay(now):
            corpse.decay()
            world.corpses.remove(corpse)


# ---------------------------------------------------------
# Command Definitions
# ---------------------------------------------------------

COMMAND_DEFS = [
    ("getcorpse", cmd_getcorpse, {"position": "standing", "help_category": "pvp"}),
    ("summoncorpse", cmd_summoncorpse, {"position": "standing", "help_category": "pvp"}),
]
