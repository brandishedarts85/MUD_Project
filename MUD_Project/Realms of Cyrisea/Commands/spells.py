"""
Realms of Cyrisea - Spell System
Full spell suite:
- Spell schools
- Elemental interactions
- Buffs & debuffs
- Healing
- Cooldowns
- Mana costs
- Spell failure
- Weather/event/faction synergy
"""

import asyncio
import random
import logging

from commands.combat import calculate_damage, apply_status, kill_target

# ---------------------------------------------------------
# Spell schools
# ---------------------------------------------------------

SPELL_SCHOOLS = {
    "pyromancy": "fire",
    "cryomancy": "ice",
    "stormcalling": "lightning",
    "venomcraft": "poison",
    "arcana": "arcane",
    "restoration": "healing",
    "warding": "buff",
}

# ---------------------------------------------------------
# Spell definitions
# ---------------------------------------------------------

SPELLS = {
    "fireball": {
        "name": "Fireball",
        "school": "pyromancy",
        "dtype": "fire",
        "mana": 20,
        "cooldown": 5,
        "power": 1.2,
        "desc": "Hurl a blazing sphere of fire.",
    },
    "frostbite": {
        "name": "Frostbite",
        "school": "cryomancy",
        "dtype": "ice",
        "mana": 15,
        "cooldown": 4,
        "power": 1.0,
        "desc": "Freeze your enemy with biting cold.",
    },
    "shock_bolt": {
        "name": "Shock Bolt",
        "school": "stormcalling",
        "dtype": "lightning",
        "mana": 18,
        "cooldown": 4,
        "power": 1.3,
        "desc": "Strike your foe with lightning.",
    },
    "venom_spit": {
        "name": "Venom Spit",
        "school": "venomcraft",
        "dtype": "poison",
        "mana": 10,
        "cooldown": 3,
        "power": 0.9,
        "desc": "Spit toxic venom.",
    },
    "arcane_blast": {
        "name": "Arcane Blast",
        "school": "arcana",
        "dtype": "arcane",
        "mana": 25,
        "cooldown": 6,
        "power": 1.4,
        "desc": "Unleash raw arcane force.",
    },
    "heal": {
        "name": "Heal",
        "school": "restoration",
        "dtype": "healing",
        "mana": 20,
        "cooldown": 5,
        "power": 1.0,
        "desc": "Restore health.",
    },
    "ward_shield": {
        "name": "Ward Shield",
        "school": "warding",
        "dtype": "buff",
        "mana": 15,
        "cooldown": 10,
        "power": 0,
        "desc": "Raise a protective barrier.",
    },
}

# ---------------------------------------------------------
# Cooldown & mana helpers
# ---------------------------------------------------------

def has_cooldown(player, spell_id):
    return player.cooldowns.get(spell_id, 0) > 0

def apply_cooldown(player, spell_id, cd):
    player.cooldowns[spell_id] = cd

def reduce_cooldowns(player):
    for s in list(player.cooldowns.keys()):
        player.cooldowns[s] -= 1
        if player.cooldowns[s] <= 0:
            del player.cooldowns[s]

# ---------------------------------------------------------
# Spell failure chance
# ---------------------------------------------------------

def spell_failure(player, spell):
    base = 5  # 5% base failure
    school = spell["school"]

    # Weather synergy
    region = getattr(player.room, "region", None)
    if region:
        weather = player.world.weather.get(region, {})
        wtype = weather.get("type")

        if wtype == "arcane_aurora" and school == "arcana":
            base -= 3
        if wtype == "storm" and school == "stormcalling":
            base -= 2
        if wtype == "blizzard" and school == "cryomancy":
            base -= 2

    # Faction synergy
    for fid, rep in player.factions.items():
        faction = player.world.factions.get(fid)
        if not faction:
            continue
        rank = player.world.get_faction_rank(faction, rep)
        abilities = faction["abilities"].get(rank, [])
        if "mana_flow" in abilities and school == "arcana":
            base -= 2

    return random.randint(1, 100) <= base

# ---------------------------------------------------------
# Cast spell
# ---------------------------------------------------------

async def cast_spell(player, spell_id, target):
    spell = SPELLS[spell_id]

    # Cooldown check
    if has_cooldown(player, spell_id):
        await player.send("That spell is still cooling down.")
        return

    # Mana check
    if player.mana < spell["mana"]:
        await player.send("You lack the mana.")
        return

    # Failure check
    if spell_failure(player, spell):
        await player.send("Your spell fizzles!")
        player.mana -= spell["mana"] // 2
        return

    # Spend mana
    player.mana -= spell["mana"]

    # Apply cooldown
    apply_cooldown(player, spell_id, spell["cooldown"])

    # Healing spell
    if spell["dtype"] == "healing":
        amount = int(player.stats.get("magic", 10) * spell["power"])
        target.hp = min(target.max_hp, target.hp + amount)
        await player.send(f"You heal {target.name} for {amount} HP.")
        await target.send(f"{player.name} heals you for {amount} HP.")
        return

    # Buff spell
    if spell["dtype"] == "buff":
        target.add_status("ward")
        await player.send(f"You shield {target.name} with arcane warding.")
        await target.send("A protective barrier surrounds you.")
        return

    # Offensive spell
    dtype = spell["dtype"]
    dmg = calculate_damage(player, target, dtype)
    dmg = int(dmg * spell["power"])

    target.hp -= dmg

    await player.send(f"You cast {spell['name']} on {target.name} for {dmg} damage.")
    await target.send(f"{player.name}'s {spell['name']} hits you for {dmg} damage.")

    await apply_status(player, target, dtype)

    if target.hp <= 0:
        await kill_target(player, target)

# ---------------------------------------------------------
# Cast command
# ---------------------------------------------------------

async def do_cast(player, args):
    """Cast a spell."""

    parts = args.split(maxsplit=1)
    if len(parts) < 2:
        await player.send("Syntax: cast <spell> <target>")
        return

    spell_id, target_name = parts
    spell_id = spell_id.lower()

    if spell_id not in SPELLS:
        await player.send("No such spell.")
        return

    target = player.room.find_player(target_name) or player.room.find_mob(target_name)
    if not target:
        await player.send("They aren't here.")
        return

    await cast_spell(player, spell_id, target)

COMMAND_DEFS = [
    ("cast", do_cast, {"position": "standing", "help_category": "spells"}),
]
