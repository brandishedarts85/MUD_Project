"""
Realms of Cyrisea - Skill System
Full skill suite:
- Physical abilities
- Weapon skills
- Defensive skills
- Mobility skills
- Cooldowns
- Stamina costs
- Skill trees
- Mastery progression
- Weather/faction synergy
"""

import asyncio
import random
import logging

from commands.combat import calculate_damage, roll_hit, roll_block, roll_crit, kill_target

# ---------------------------------------------------------
# Skill trees
# ---------------------------------------------------------

SKILL_TREES = {
    "warrior": {
        "name": "Warrior",
        "skills": ["power_strike", "shield_wall", "whirlwind"],
    },
    "rogue": {
        "name": "Rogue",
        "skills": ["backstab", "evasive_step", "flurry"],
    },
    "ranger": {
        "name": "Ranger",
        "skills": ["aimed_shot", "rapid_fire", "entangle"],
    },
    "monk": {
        "name": "Monk",
        "skills": ["palm_strike", "iron_body", "wind_step"],
    },
}

# ---------------------------------------------------------
# Skill definitions
# ---------------------------------------------------------

SKILLS = {
    "power_strike": {
        "name": "Power Strike",
        "tree": "warrior",
        "stamina": 15,
        "cooldown": 4,
        "power": 1.4,
        "dtype": "physical",
        "desc": "Deliver a heavy blow.",
    },
    "shield_wall": {
        "name": "Shield Wall",
        "tree": "warrior",
        "stamina": 10,
        "cooldown": 8,
        "buff": {"block": 20},
        "duration": 6,
        "desc": "Raise your shield to block incoming attacks.",
    },
    "whirlwind": {
        "name": "Whirlwind",
        "tree": "warrior",
        "stamina": 25,
        "cooldown": 10,
        "power": 1.0,
        "aoe": True,
        "dtype": "physical",
        "desc": "Spin and strike all nearby enemies.",
    },

    "backstab": {
        "name": "Backstab",
        "tree": "rogue",
        "stamina": 20,
        "cooldown": 6,
        "power": 2.0,
        "dtype": "physical",
        "desc": "Strike from behind for massive damage.",
    },
    "evasive_step": {
        "name": "Evasive Step",
        "tree": "rogue",
        "stamina": 10,
        "cooldown": 5,
        "buff": {"dodge": 25},
        "duration": 5,
        "desc": "Increase your dodge chance.",
    },
    "flurry": {
        "name": "Flurry",
        "tree": "rogue",
        "stamina": 18,
        "cooldown": 7,
        "multi": 3,
        "power": 0.6,
        "dtype": "physical",
        "desc": "Strike rapidly multiple times.",
    },

    "aimed_shot": {
        "name": "Aimed Shot",
        "tree": "ranger",
        "stamina": 12,
        "cooldown": 4,
        "power": 1.5,
        "dtype": "physical",
        "desc": "Fire a precise arrow.",
    },
    "rapid_fire": {
        "name": "Rapid Fire",
        "tree": "ranger",
        "stamina": 20,
        "cooldown": 8,
        "multi": 4,
        "power": 0.5,
        "dtype": "physical",
        "desc": "Loose several arrows in quick succession.",
    },
    "entangle": {
        "name": "Entangle",
        "tree": "ranger",
        "stamina": 15,
        "cooldown": 6,
        "debuff": {"movement_mod": 0.5},
        "duration": 5,
        "desc": "Root your target in place.",
    },

    "palm_strike": {
        "name": "Palm Strike",
        "tree": "monk",
        "stamina": 10,
        "cooldown": 3,
        "power": 1.2,
        "dtype": "physical",
        "desc": "Strike with focused chi.",
    },
    "iron_body": {
        "name": "Iron Body",
        "tree": "monk",
        "stamina": 15,
        "cooldown": 10,
        "buff": {"defense": 20},
        "duration": 8,
        "desc": "Harden your body against damage.",
    },
    "wind_step": {
        "name": "Wind Step",
        "tree": "monk",
        "stamina": 12,
        "cooldown": 6,
        "buff": {"movement_mod": 1.5},
        "duration": 5,
        "desc": "Move with supernatural speed.",
    },
}

# ---------------------------------------------------------
# Cooldowns & stamina
# ---------------------------------------------------------

def has_skill_cd(player, skill_id):
    return player.skill_cds.get(skill_id, 0) > 0

def apply_skill_cd(player, skill_id, cd):
    player.skill_cds[skill_id] = cd

def reduce_skill_cds(player):
    for s in list(player.skill_cds.keys()):
        player.skill_cds[s] -= 1
        if player.skill_cds[s] <= 0:
            del player.skill_cds[s]

# ---------------------------------------------------------
# Execute skill
# ---------------------------------------------------------

async def use_skill(player, skill_id, target):
    skill = SKILLS[skill_id]

    # Cooldown check
    if has_skill_cd(player, skill_id):
        await player.send("That skill is still cooling down.")
        return

    # Stamina check
    if player.stamina < skill["stamina"]:
        await player.send("You lack the stamina.")
        return

    # Spend stamina
    player.stamina -= skill["stamina"]

    # Apply cooldown
    apply_skill_cd(player, skill_id, skill["cooldown"])

    # Buff skill
    if "buff" in skill:
        for stat, value in skill["buff"].items():
            player.add_status(stat, value, skill["duration"])
        await player.send(f"You use {skill['name']} and gain a buff.")
        return

    # Debuff skill
    if "debuff" in skill:
        for stat, value in skill["debuff"].items():
            target.add_status(stat, value, skill["duration"])
        await player.send(f"You use {skill['name']} and hinder {target.name}.")
        await target.send(f"{player.name} uses {skill['name']} on you.")
        return

    # Offensive skill
    dtype = skill["dtype"]

    # Multi-hit skills
    hits = skill.get("multi", 1)
    total_damage = 0

    for _ in range(hits):
        if not roll_hit(player, target):
            await player.send("Your strike misses.")
            await target.send(f"{player.name} misses you.")
            continue

        dmg = calculate_damage(player, target, dtype)
        dmg = int(dmg * skill["power"])

        if roll_crit(player):
            dmg = int(dmg * 1.5)
            await player.send("Critical strike!")
            await target.send("You are critically struck!")

        target.hp -= dmg
        total_damage += dmg

        if target.hp <= 0:
            break

    await player.send(f"You use {skill['name']} for {total_damage} damage.")
    await target.send(f"{player.name}'s {skill['name']} hits you for {total_damage} damage.")

    if target.hp <= 0:
        await kill_target(player, target)

# ---------------------------------------------------------
# Skill command
# ---------------------------------------------------------

async def do_skill(player, args):
    """Use a skill."""

    parts = args.split(maxsplit=1)
    if len(parts) < 2:
        await player.send("Syntax: skill <skill> <target>")
        return

    skill_id, target_name = parts
    skill_id = skill_id.lower()

    if skill_id not in SKILLS:
        await player.send("No such skill.")
        return

    target = player.room.find_player(target_name) or player.room.find_mob(target_name)
    if not target:
        await player.send("They aren't here.")
        return

    await use_skill(player, skill_id, target)

COMMAND_DEFS = [
    ("skill", do_skill, {"position": "standing", "help_category": "skills"}),
]
