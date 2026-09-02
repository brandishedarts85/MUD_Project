"""
Realms of Cyrisea - Magic Commands
Enhanced magic system:
- Elemental spell types
- Resistances & vulnerabilities
- Mana cost scaling
- Spell failure chance
- Buff/debuff durations
- Terrain interaction
"""

import asyncio
import random
import logging


# Elemental damage modifiers based on terrain
TERRAIN_MAGIC_MOD = {
    "forest": {"fire": 0.8, "ice": 1.1, "arcane": 1.0},
    "swamp": {"fire": 0.7, "ice": 1.0, "arcane": 1.2},
    "mountain": {"fire": 1.2, "ice": 0.9, "arcane": 1.0},
    "desert": {"fire": 1.3, "ice": 0.7, "arcane": 1.0},
    "city": {"fire": 1.0, "ice": 1.0, "arcane": 1.0},
    "indoors": {"fire": 1.0, "ice": 1.0, "arcane": 1.0},
    "road": {"fire": 1.0, "ice": 1.0, "arcane": 1.0},
    "field": {"fire": 1.0, "ice": 1.0, "arcane": 1.0},
}


# Spell definitions
SPELLS = {
    "fireball": {
        "element": "fire",
        "mana": 15,
        "base": (20, 40),
        "fail": 10,  # 10% failure chance
        "help": "Hurl a ball of fire at your enemy."
    },
    "icebolt": {
        "element": "ice",
        "mana": 12,
        "base": (15, 30),
        "fail": 8,
        "help": "Launch a shard of ice at your enemy."
    },
    "arcane_missile": {
        "element": "arcane",
        "mana": 10,
        "base": (10, 25),
        "fail": 5,
        "help": "Strike your enemy with pure arcane force."
    },
    "heal": {
        "element": "holy",
        "mana": 12,
        "base": (20, 35),
        "fail": 5,
        "help": "Restore your health with divine energy."
    },
    "haste": {
        "element": "arcane",
        "mana": 8,
        "base": (0, 0),
        "fail": 10,
        "buff": {"speed": 1.5, "duration": 30},
        "help": "Increase your combat speed temporarily."
    },
}


async def cast_damage_spell(player, target, spell):
    """Handle offensive spells."""

    element = spell["element"]
    mana_cost = spell["mana"]

    # Check mana
    if player.mana < mana_cost:
        await player.send("You lack the mana to cast that spell.")
        return

    # Spell failure
    if random.randint(1, 100) <= spell["fail"]:
        await player.send("Your spell fizzles and fails.")
        player.mana -= mana_cost // 2
        return

    player.mana -= mana_cost

    # Base damage
    base_min, base_max = spell["base"]
    damage = random.randint(base_min, base_max)

    # Terrain modifier
    terrain = player.room.sector or "field"
    terrain_mod = TERRAIN_MAGIC_MOD.get(terrain, {}).get(element, 1.0)
    damage = int(damage * terrain_mod)

    # Target resistances/vulnerabilities
    if hasattr(target, "resist") and element in target.resist:
        damage = int(damage * 0.7)
    if hasattr(target, "vulnerable") and element in target.vulnerable:
        damage = int(damage * 1.3)

    # Apply damage
    target.hp -= damage

    await player.send(f"You cast {spell['help']} ({damage} damage).")
    await target.send(f"{player.name}'s {element} spell hits you for {damage} damage!")

    # Death check
    if target.hp <= 0:
        await target.send("You have been slain by magic!")
        await player.send(f"You have slain {target.name} with your spell!")
        target.room = None


async def cast_heal_spell(player, spell):
    """Handle healing spells."""

    mana_cost = spell["mana"]

    if player.mana < mana_cost:
        await player.send("You lack the mana to cast that spell.")
        return

    if random.randint(1, 100) <= spell["fail"]:
        await player.send("Your healing spell fizzles.")
        player.mana -= mana_cost // 2
        return

    player.mana -= mana_cost

    heal_min, heal_max = spell["base"]
    heal_amount = random.randint(heal_min, heal_max)

    player.hp = min(player.max_hp, player.hp + heal_amount)

    await player.send(f"You restore {heal_amount} health.")


async def cast_buff_spell(player, spell):
    """Handle buff spells like haste."""

    mana_cost = spell["mana"]

    if player.mana < mana_cost:
        await player.send("You lack the mana to cast that spell.")
        return

    if random.randint(1, 100) <= spell["fail"]:
        await player.send("Your spell fizzles.")
        player.mana -= mana_cost // 2
        return

    player.mana -= mana_cost

    buff = spell["buff"]
    player.buffs.append(buff)

    await player.send(f"You feel {spell['help'].lower()}")

    # Buff expiration
    async def expire_buff():
        await asyncio.sleep(buff["duration"])
        player.buffs.remove(buff)
        await player.send("Your magical enhancement fades.")

    asyncio.create_task(expire_buff())


async def do_cast(player, args):
    """Main cast command."""

    if not args:
        await player.send("Cast what.")
        return

    parts = args.split(maxsplit=1)
    spell_name = parts[0].lower()
    target_name = parts[1] if len(parts) > 1 else None

    spell = SPELLS.get(spell_name)
    if not spell:
        await player.send("You don't know that spell.")
        return

    # Healing spell
    if spell_name == "heal":
        await cast_heal_spell(player, spell)
        return

    # Buff spell
    if "buff" in spell:
        await cast_buff_spell(player, spell)
        return

    # Offensive spell
    if not target_name:
        await player.send("Cast it at whom.")
        return

    target = player.room.find_mob(target_name) or player.room.find_player(target_name)

    if not target:
        await player.send("They aren't here.")
        return

    await cast_damage_spell(player, target, spell)


# Command definitions
COMMAND_DEFS = [
    ("cast", do_cast, {"position": "standing", "help_category": "magic"}),
]
