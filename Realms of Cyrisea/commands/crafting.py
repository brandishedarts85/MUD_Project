"""
Realms of Cyrisea - Crafting System
Full crafting suite:
- Crafting professions
- Crafting mastery & skill trees
- Crafting quality & rarity
- Crafting materials
- Crafting stations
- Crafting recipes
- Enhancements (runes, socketing, reforging, infusions)
- Crafting economy integration
- Crafting quests & achievements hooks
"""

import asyncio
import logging
import random

log = logging.getLogger(__name__)

# ---------------------------------------------------------
# Profession definitions
# ---------------------------------------------------------

PROFESSIONS = {
    "blacksmith": {
        "name": "Blacksmith",
        "desc": "Forging weapons, armor, and metal tools.",
        "primary_materials": ["metal", "ore", "flux"],
    },
    "enchanter": {
        "name": "Enchanter",
        "desc": "Imbuing items with arcane properties.",
        "primary_materials": ["arcane_dust", "crystal", "essence"],
    },
    "alchemist": {
        "name": "Alchemist",
        "desc": "Brewing potions, elixirs, and reagents.",
        "primary_materials": ["herb", "reagent", "essence"],
    },
    "leatherworker": {
        "name": "Leatherworker",
        "desc": "Crafting light armor and bags.",
        "primary_materials": ["hide", "cloth", "thread"],
    },
    "woodworker": {
        "name": "Woodworker",
        "desc": "Creating staves, bows, and wooden implements.",
        "primary_materials": ["wood", "resin", "fiber"],
    },
    "jewelcrafter": {
        "name": "Jewelcrafter",
        "desc": "Setting gems and crafting rings, amulets.",
        "primary_materials": ["gem", "metal", "essence"],
    },
}

# ---------------------------------------------------------
# Profession mastery & skill trees
# ---------------------------------------------------------

PROFESSION_SKILL_TREES = {
    "blacksmith": {
        "nodes": {
            "efficiency_1": {"desc": "Reduce material cost by 5%.", "cost": 1},
            "efficiency_2": {"desc": "Reduce material cost by 10%.", "cost": 2},
            "quality_1": {"desc": "Increase base quality by 1 tier.", "cost": 2},
            "rarity_1": {"desc": "Increase rare roll chance by 5%.", "cost": 3},
            "socket_mastery": {"desc": "Increase socket count by 1.", "cost": 3},
        },
        "links": {
            "efficiency_1": ["efficiency_2", "quality_1"],
            "quality_1": ["rarity_1", "socket_mastery"],
        },
    },
    "enchanter": {
        "nodes": {
            "essence_control": {"desc": "Reduce essence cost by 10%.", "cost": 2},
            "power_runes": {"desc": "Increase rune potency by 10%.", "cost": 3},
            "stability": {"desc": "Reduce corruption chance when reforging.", "cost": 3},
        },
        "links": {
            "essence_control": ["power_runes", "stability"],
        },
    },
    # Other professions can be expanded similarly
}

# ---------------------------------------------------------
# Quality & rarity tiers
# ---------------------------------------------------------

QUALITY_TIERS = ["poor", "normal", "fine", "superior", "masterwork", "legendary"]
RARITY_TIERS = ["common", "uncommon", "rare", "epic", "legendary"]

QUALITY_MODS = {
    "poor": 0.8,
    "normal": 1.0,
    "fine": 1.1,
    "superior": 1.2,
    "masterwork": 1.35,
    "legendary": 1.5,
}

RARITY_SOCKET_BASE = {
    "common": 0,
    "uncommon": 1,
    "rare": 2,
    "epic": 3,
    "legendary": 4,
}

# ---------------------------------------------------------
# Materials
# ---------------------------------------------------------

MATERIALS = {
    "heartwood_timber": {
        "type": "wood",
        "tier": 3,
        "regions": ["crystalwood"],
        "rarity": "rare",
        "affinity": ["nature"],
    },
    "obsidian_flux": {
        "type": "flux",
        "tier": 4,
        "regions": ["obsidian_order"],
        "rarity": "epic",
        "affinity": ["arcane"],
    },
    "crystalwood_resin": {
        "type": "resin",
        "tier": 2,
        "regions": ["crystalwood"],
        "rarity": "uncommon",
        "affinity": ["nature"],
    },
    "frostpeak_ice_core": {
        "type": "essence",
        "tier": 4,
        "regions": ["frostpeak"],
        "rarity": "epic",
        "affinity": ["frost"],
    },
    "sunspire_silk": {
        "type": "cloth",
        "tier": 3,
        "regions": ["sunspire"],
        "rarity": "rare",
        "affinity": ["trade"],
    },
    "arcane_dust": {
        "type": "arcane_dust",
        "tier": 2,
        "regions": ["obsidian_order"],
        "rarity": "common",
        "affinity": ["arcane"],
    },
}

# ---------------------------------------------------------
# Crafting stations
# ---------------------------------------------------------

CRAFTING_STATIONS = {
    "forge": {
        "name": "Forge",
        "professions": ["blacksmith", "jewelcrafter"],
        "quality_bonus": 0.05,
        "rarity_bonus": 0.03,
    },
    "arcane_font": {
        "name": "Arcane Font",
        "professions": ["enchanter"],
        "quality_bonus": 0.05,
        "rarity_bonus": 0.05,
    },
    "alchemy_table": {
        "name": "Alchemy Table",
        "professions": ["alchemist"],
        "quality_bonus": 0.03,
        "rarity_bonus": 0.02,
    },
    "workbench": {
        "name": "Workbench",
        "professions": ["woodworker", "leatherworker"],
        "quality_bonus": 0.03,
        "rarity_bonus": 0.02,
    },
}

# ---------------------------------------------------------
# Recipes
# ---------------------------------------------------------

RECIPES = {
    "iron_sword": {
        "name": "Iron Sword",
        "profession": "blacksmith",
        "station": "forge",
        "base_item_vnum": 2001,
        "materials": {
            "metal": 3,
            "flux": 1,
        },
        "base_quality": "normal",
        "base_rarity": "common",
    },
    "heartwood_staff": {
        "name": "Heartwood Staff",
        "profession": "woodworker",
        "station": "workbench",
        "base_item_vnum": 2002,
        "materials": {
            "wood": 4,
            "resin": 2,
        },
        "base_quality": "fine",
        "base_rarity": "uncommon",
    },
    "obsidian_runeblade": {
        "name": "Obsidian Runeblade",
        "profession": "blacksmith",
        "station": "forge",
        "base_item_vnum": 2003,
        "materials": {
            "metal": 5,
            "obsidian_flux": 2,
            "arcane_dust": 3,
        },
        "base_quality": "superior",
        "base_rarity": "rare",
    },
}

# ---------------------------------------------------------
# Enhancements: runes, infusions, reforging
# ---------------------------------------------------------

RUNES = {
    "rune_of_flame": {
        "name": "Rune of Flame",
        "element": "fire",
        "power": 1.1,
        "desc": "Adds fire damage.",
    },
    "rune_of_frost": {
        "name": "Rune of Frost",
        "element": "frost",
        "power": 1.1,
        "desc": "Adds frost damage.",
    },
    "rune_of_focus": {
        "name": "Rune of Focus",
        "element": "arcane",
        "power": 1.05,
        "desc": "Increases spell power.",
    },
}

INFUSIONS = {
    "shadow_infusion": {
        "name": "Shadow Infusion",
        "source": "shadow_rift",
        "effect": {"shadow_damage": 5, "corruption_chance": 0.1},
    },
    "arcane_infusion": {
        "name": "Arcane Infusion",
        "source": "arcane_node",
        "effect": {"magic_power": 5},
    },
    "frost_infusion": {
        "name": "Frost Infusion",
        "source": "frostpeak",
        "effect": {"frost_resist": 10},
    },
}

# ---------------------------------------------------------
# Player crafting state helpers
# ---------------------------------------------------------

def get_profession(player, name):
    return player.professions.get(name)


def add_profession(player, name):
    if name not in PROFESSIONS:
        return False
    if name in player.professions:
        return False
    player.professions[name] = {
        "level": 1,
        "xp": 0,
        "skill_nodes": set(),
    }
    return True


def gain_profession_xp(player, name, amount):
    prof = get_profession(player, name)
    if not prof:
        return
    prof["xp"] += amount
    # Simple level curve: 100 xp per level
    while prof["xp"] >= prof["level"] * 100:
        prof["xp"] -= prof["level"] * 100
        prof["level"] += 1


def unlock_skill_node(player, profession, node_id):
    tree = PROFESSION_SKILL_TREES.get(profession)
    if not tree or node_id not in tree["nodes"]:
        return False
    prof = get_profession(player, profession)
    if not prof:
        return False
    prof["skill_nodes"].add(node_id)
    return True

# ---------------------------------------------------------
# Core crafting logic
# ---------------------------------------------------------

def _get_station_bonus(player, recipe):
    station_id = recipe["station"]
    station = CRAFTING_STATIONS.get(station_id)
    if not station:
        return 0.0, 0.0

    # Housing / world bonuses could be added here
    return station["quality_bonus"], station["rarity_bonus"]


def _get_profession_mods(player, recipe):
    prof_name = recipe["profession"]
    prof = get_profession(player, prof_name)
    if not prof:
        return 0.0, 0.0

    quality_bonus = 0.0
    rarity_bonus = 0.0

    # Example: skill nodes influence bonuses
    nodes = prof["skill_nodes"]
    if "quality_1" in nodes:
        quality_bonus += 0.05
    if "rarity_1" in nodes:
        rarity_bonus += 0.05
    if "efficiency_2" in nodes:
        # Efficiency would reduce material cost; handled elsewhere
        pass

    return quality_bonus, rarity_bonus


def _roll_quality(base_quality, quality_bonus):
    idx = QUALITY_TIERS.index(base_quality)
    # Each 0.05 bonus gives a chance to step up one tier
    steps = int(quality_bonus / 0.05)
    for _ in range(steps):
        if idx < len(QUALITY_TIERS) - 1 and random.random() < 0.5:
            idx += 1
    return QUALITY_TIERS[idx]


def _roll_rarity(base_rarity, rarity_bonus):
    idx = RARITY_TIERS.index(base_rarity)
    steps = int(rarity_bonus / 0.05)
    for _ in range(steps):
        if idx < len(RARITY_TIERS) - 1 and random.random() < 0.4:
            idx += 1
    return RARITY_TIERS[idx]


def _calculate_sockets(rarity, prof):
    base = RARITY_SOCKET_BASE[rarity]
    if prof and "socket_mastery" in prof["skill_nodes"]:
        base += 1
    return base


async def craft_item(player, recipe_id):
    if recipe_id not in RECIPES:
        await player.send("No such recipe.")
        return

    recipe = RECIPES[recipe_id]
    prof_name = recipe["profession"]

    if prof_name not in player.professions:
        await player.send("You do not know that profession.")
        return

    # Check station
    station = recipe["station"]
    if not getattr(player.room, "crafting_station", None) == station:
        await player.send(f"You must be at a {CRAFTING_STATIONS[station]['name']} to craft this.")
        return

    # Check materials (simplified: count by type)
    needed = recipe["materials"].copy()
    inventory_map = {}

    for obj in list(player.inventory):
        mtype = getattr(obj, "material_type", None)
        if not mtype:
            continue
        inventory_map.setdefault(mtype, []).append(obj)

    for mtype, count in needed.items():
        if len(inventory_map.get(mtype, [])) < count:
            await player.send(f"You lack enough {mtype} to craft {recipe['name']}.")
            return

    # Consume materials
    for mtype, count in needed.items():
        for _ in range(count):
            obj = inventory_map[mtype].pop()
            player.inventory.remove(obj)

    # Calculate bonuses
    station_qb, station_rb = _get_station_bonus(player, recipe)
    prof_qb, prof_rb = _get_profession_mods(player, recipe)

    total_qb = station_qb + prof_qb
    total_rb = station_rb + prof_rb

    # Roll quality & rarity
    quality = _roll_quality(recipe["base_quality"], total_qb)
    rarity = _roll_rarity(recipe["base_rarity"], total_rb)

    # Create item
    base_obj = player.world.objects.get(recipe["base_item_vnum"])
    if not base_obj:
        await player.send("The crafting energies fail to coalesce.")
        return

    new_item = base_obj.clone()
    new_item.quality = quality
    new_item.rarity = rarity

    # Apply stat scaling
    mod = QUALITY_MODS[quality]
    if hasattr(new_item, "stats"):
        for k, v in new_item.stats.items():
            new_item.stats[k] = int(v * mod)

    # Sockets
    prof = get_profession(player, prof_name)
    new_item.sockets = _calculate_sockets(rarity, prof)
    new_item.runes = []

    player.inventory.append(new_item)
    await player.send(f"You craft {new_item.short_desc} ({quality.title()}, {rarity.title()}).")

    # Gain profession XP
    gain_profession_xp(player, prof_name, 20)

# ---------------------------------------------------------
# Socketing & runes
# ---------------------------------------------------------

async def socket_rune(player, item_name, rune_id):
    # Find item
    target = None
    for obj in player.inventory:
        if item_name.lower() in obj.short_desc.lower():
            target = obj
            break

    if not target:
        await player.send("You don't have that item.")
        return

    if not hasattr(target, "sockets"):
        await player.send("That item cannot have sockets.")
        return

    if len(getattr(target, "runes", [])) >= target.sockets:
        await player.send("All sockets are filled.")
        return

    if rune_id not in RUNES:
        await player.send("No such rune.")
        return

    # Check rune in inventory
    rune_obj = None
    for obj in player.inventory:
        if getattr(obj, "rune_id", None) == rune_id:
            rune_obj = obj
            break

    if not rune_obj:
        await player.send("You do not possess that rune.")
        return

    # Consume rune
    player.inventory.remove(rune_obj)

    # Apply rune
    rune = RUNES[rune_id]
    target.runes.append(rune_id)

    # Simple stat effect example
    if hasattr(target, "stats"):
        if rune["element"] == "fire":
            target.stats["fire_damage"] = target.stats.get("fire_damage", 0) + 5
        if rune["element"] == "frost":
            target.stats["frost_damage"] = target.stats.get("frost_damage", 0) + 5
        if rune["element"] == "arcane":
            target.stats["magic_power"] = target.stats.get("magic_power", 0) + 3

    await player.send(f"You socket {rune['name']} into {target.short_desc}.")

# ---------------------------------------------------------
# Reforging
# ---------------------------------------------------------

async def reforge_item(player, item_name):
    target = None
    for obj in player.inventory:
        if item_name.lower() in obj.short_desc.lower():
            target = obj
            break

    if not target or not hasattr(target, "stats"):
        await player.send("You cannot reforge that.")
        return

    # Check enchanter profession
    prof = get_profession(player, "enchanter")
    if not prof:
        await player.send("You must be an enchanter to reforge items.")
        return

    # Corruption chance
    base_corrupt = 0.2
    if "stability" in prof["skill_nodes"]:
        base_corrupt -= 0.1

    if random.random() < base_corrupt:
        # Corruption: reduce one random stat
        if target.stats:
            stat = random.choice(list(target.stats.keys()))
            target.stats[stat] = max(1, int(target.stats[stat] * 0.7))
            await player.send(f"The reforging goes awry! {stat} is weakened.")
        return

    # Successful reroll: boost one random stat
    if target.stats:
        stat = random.choice(list(target.stats.keys()))
        target.stats[stat] = int(target.stats[stat] * 1.2)
        await player.send(f"The reforging succeeds! {stat} is strengthened.")

    gain_profession_xp(player, "enchanter", 15)

# ---------------------------------------------------------
# Infusions
# ---------------------------------------------------------

async def infuse_item(player, item_name, infusion_id):
    target = None
    for obj in player.inventory:
        if item_name.lower() in obj.short_desc.lower():
            target = obj
            break

    if not target:
        await player.send("You don't have that item.")
        return

    if infusion_id not in INFUSIONS:
        await player.send("No such infusion.")
        return

    infusion = INFUSIONS[infusion_id]

    # Check world state source
    world = player.world
    source = infusion["source"]

    if source == "shadow_rift" and not world.state["environment"]["shadow_rifts"]:
        await player.send("No active shadow rifts to draw from.")
        return
    if source == "arcane_node" and not world.state["environment"]["arcane_nodes"]:
        await player.send("No active arcane nodes to draw from.")
        return
    if source == "frostpeak" and world.state["regions"]["frostpeak"]["frozen_corruption"] < 20:
        await player.send("The frost energies are too weak to infuse.")
        return

    # Apply infusion
    if not hasattr(target, "infusions"):
        target.infusions = []
    target.infusions.append(infusion_id)

    if hasattr(target, "stats"):
        for k, v in infusion["effect"].items():
            if isinstance(v, int):
                target.stats[k] = target.stats.get(k, 0) + v

    await player.send(f"You infuse {target.short_desc} with {infusion['name']}.")

# ---------------------------------------------------------
# Economy hooks (simplified)
# ---------------------------------------------------------

def get_crafting_value(item):
    """Estimate value based on quality, rarity, and enhancements."""
    base = getattr(item, "base_value", 10)
    qmod = QUALITY_MODS.get(getattr(item, "quality", "normal"), 1.0)
    rmod = 1.0 + 0.1 * RARITY_TIERS.index(getattr(item, "rarity", "common"))
    rune_bonus = 5 * len(getattr(item, "runes", []))
    infusion_bonus = 10 * len(getattr(item, "infusions", []))
    return int(base * qmod * rmod + rune_bonus + infusion_bonus)

# ---------------------------------------------------------
# Player commands
# ---------------------------------------------------------

async def do_professions(player, args):
    """List your crafting professions."""
    if not player.professions:
        await player.send("You have no crafting professions.")
        return

    await player.send("\033[95mCrafting Professions:\033[0m")
    for name, data in player.professions.items():
        await player.send(f"{PROFESSIONS[name]['name']}: level {data['level']} (xp {data['xp']})")


async def do_profession(player, args):
    """Show a profession's skill tree."""
    if not args:
        await player.send("Profession which?")
        return

    name = args.lower()
    if name not in PROFESSIONS:
        await player.send("No such profession.")
        return

    tree = PROFESSION_SKILL_TREES.get(name)
    await player.send(f"\033[94m{PROFESSIONS[name]['name']} Skill Tree\033[0m")
    if not tree:
        await player.send("No skill tree defined yet.")
        return

    for nid, node in tree["nodes"].items():
        await player.send(f"- {nid}: {node['desc']} (cost {node['cost']})")


async def do_learnprof(player, args):
    """Learn a new profession."""
    if not args:
        await player.send("Learn which profession?")
        return

    name = args.lower()
    if add_profession(player, name):
        await player.send(f"You learn the profession: {PROFESSIONS[name]['name']}.")
    else:
        await player.send("You cannot learn that profession.")


async def do_craft(player, args):
    """Craft an item from a recipe."""
    if not args:
        await player.send("Craft which recipe?")
        return

    await craft_item(player, args.lower())


async def do_socket(player, args):
    """Socket a rune into an item."""
    parts = args.split()
    if len(parts) != 2:
        await player.send("Syntax: socket <item> <rune_id>")
        return

    item_name, rune_id = parts
    await socket_rune(player, item_name, rune_id)


async def do_reforge(player, args):
    """Reforge an item."""
    if not args:
        await player.send("Reforge which item?")
        return

    await reforge_item(player, args)


async def do_infuse(player, args):
    """Infuse an item with world energy."""
    parts = args.split()
    if len(parts) != 2:
        await player.send("Syntax: infuse <item> <infusion_id>")
        return

    item_name, infusion_id = parts
    await infuse_item(player, item_name, infusion_id)

# ---------------------------------------------------------
# Command definitions
# ---------------------------------------------------------

COMMAND_DEFS = [
    ("professions", do_professions, {"position": "standing", "help_category": "crafting"}),
    ("profession",  do_profession,  {"position": "standing", "help_category": "crafting"}),
    ("learnprof",   do_learnprof,   {"position": "standing", "help_category": "crafting"}),
    ("craft",       do_craft,       {"position": "standing", "help_category": "crafting"}),
    ("socket",      do_socket,      {"position": "standing", "help_category": "crafting"}),
    ("reforge",     do_reforge,     {"position": "standing", "help_category": "crafting"}),
    ("infuse",      do_infuse,      {"position": "standing", "help_category": "crafting"}),
]
