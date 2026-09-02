"""
Realms of Cyrisea - Travel & Movement System
Grand travel suite:
- Terrain & movement cost
- Stamina & speed
- Mounts (rarity, abilities, breeding, equipment)
- Rideable pets
- Boats, ferries, ships
- Portals & teleportation rules
- Flight system
- Caravans & escorts
- Weather-based travel hazards
- Faction/guild travel perks
- Fast-travel unlocks
- Travel achievements & titles
- Travel professions (Pathfinder, Navigator, Beast Rider)
"""

import asyncio
import logging
import random

log = logging.getLogger(__name__)

# ---------------------------------------------------------
# Terrain types
# ---------------------------------------------------------

TERRAIN = {
    "road": {"cost": 1, "speed_mod": 1.0},
    "forest": {"cost": 2, "speed_mod": 0.9},
    "swamp": {"cost": 3, "speed_mod": 0.7},
    "mountain": {"cost": 4, "speed_mod": 0.6},
    "snow": {"cost": 3, "speed_mod": 0.8},
    "desert": {"cost": 3, "speed_mod": 0.75},
    "water": {"cost": 99, "speed_mod": 0.0},  # requires boat
    "air": {"cost": 1, "speed_mod": 1.5},     # flight
}

# ---------------------------------------------------------
# Stamina
# ---------------------------------------------------------

def movement_stamina_cost(player, terrain):
    base = TERRAIN[terrain]["cost"]
    # Mount reduces cost
    if player.mount:
        base = max(1, base - player.mount["stamina_reduction"])
    # Travel profession reduces cost
    if "pathfinder" in player.travel_professions:
        base = max(1, base - 1)
    return base

def reduce_stamina(player, amount):
    player.stamina = max(0, player.stamina - amount)
    return player.stamina

# ---------------------------------------------------------
# Mount definitions
# ---------------------------------------------------------

MOUNTS = {
    "forest_stag": {
        "name": "Forest Stag",
        "rarity": "uncommon",
        "speed": 1.2,
        "stamina_reduction": 1,
        "abilities": ["leap"],
        "breed_group": "nature",
    },
    "sunspire_courser": {
        "name": "Sunspire Courser",
        "rarity": "rare",
        "speed": 1.3,
        "stamina_reduction": 2,
        "abilities": ["dash"],
        "breed_group": "speed",
    },
    "obsidian_drake": {
        "name": "Obsidian Drake",
        "rarity": "epic",
        "speed": 1.5,
        "stamina_reduction": 2,
        "abilities": ["flight", "arcane_burst"],
        "breed_group": "arcane",
    },
    "frostpeak_mammoth": {
        "name": "Frostpeak Mammoth",
        "rarity": "legendary",
        "speed": 1.1,
        "stamina_reduction": 3,
        "abilities": ["trample"],
        "breed_group": "frost",
    },
}

MOUNT_EQUIPMENT = {
    "saddle_basic": {"speed_mod": 0.05},
    "saddle_masterwork": {"speed_mod": 0.1},
    "reinforced_harness": {"stamina_mod": 1},
}

# ---------------------------------------------------------
# Rideable pets
# ---------------------------------------------------------

RIDEABLE_PETS = ["ember_pup", "obsidian_imp"]  # example

# ---------------------------------------------------------
# Boats & ships
# ---------------------------------------------------------

BOATS = {
    "rowboat": {"speed": 1.0},
    "sunspire_sloop": {"speed": 1.3},
    "obsidian_galley": {"speed": 1.5},
}

FERRIES = {
    "sunspire_ferry": {
        "from": 3001,
        "to": 3002,
        "cost": 10,
        "time": 10,
    }
}

# ---------------------------------------------------------
# Portals
# ---------------------------------------------------------

PORTALS = {
    "crystalwood_portal": {
        "from": 1201,
        "to": 9001,
        "requires": {"faction_rep": ("crystalwood", 250)},
    },
    "obsidian_gate": {
        "from": 2101,
        "to": 9500,
        "requires": {"item": 7001},
    },
}

# ---------------------------------------------------------
# Flight
# ---------------------------------------------------------

def can_fly(player):
    if player.mount and "flight" in player.mount["abilities"]:
        return True
    if player.pet and player.pet.get("can_fly"):
        return True
    return False

# ---------------------------------------------------------
# Caravans
# ---------------------------------------------------------

CARAVANS = {
    "sunspire_trade_route": {
        "start": 3001,
        "end": 3005,
        "reward": {"gold": 50, "rep": ("sunspire", 20)},
        "danger": 0.2,
    }
}

# ---------------------------------------------------------
# Weather hazards
# ---------------------------------------------------------

def weather_speed_penalty(world, region):
    weather = world.weather.get(region, "clear")
    if weather == "storm":
        return 0.8
    if weather == "snow":
        return 0.85
    if weather == "heatwave":
        return 0.9
    return 1.0

# ---------------------------------------------------------
# Travel perks
# ---------------------------------------------------------

def faction_travel_bonus(player, region):
    if player.factions.get(region, 0) >= 500:
        return 1.1
    return 1.0

def guild_travel_bonus(player):
    if player.guild_rank == "Officer":
        return 1.05
    if player.guild_rank == "Leader":
        return 1.1
    return 1.0

# ---------------------------------------------------------
# Fast travel
# ---------------------------------------------------------

FAST_TRAVEL_POINTS = {
    "crystalwood_glade": 1201,
    "sunspire_harbor": 3001,
    "obsidian_spire": 2101,
}

def has_fast_travel(player, point):
    return point in player.fast_travel_unlocks

# ---------------------------------------------------------
# Travel professions
# ---------------------------------------------------------

TRAVEL_PROFESSIONS = {
    "pathfinder": {"desc": "Expert in terrain navigation."},
    "navigator": {"desc": "Master of sea and sky routes."},
    "beast_rider": {"desc": "Specialist in mounts and rideable beasts."},
}

# ---------------------------------------------------------
# Movement
# ---------------------------------------------------------

async def do_move(player, direction):
    room = player.room
    exit = room.exits.get(direction)
    if not exit:
        await player.send("You cannot go that way.")
        return

    next_room = exit["room"]
    terrain = getattr(next_room, "terrain", "road")

    # Stamina cost
    cost = movement_stamina_cost(player, terrain)
    if player.stamina < cost:
        await player.send("You are too exhausted to travel.")
        return

    reduce_stamina(player, cost)

    # Speed modifiers
    speed = TERRAIN[terrain]["speed_mod"]
    if player.mount:
        speed *= player.mount["speed"]
    speed *= weather_speed_penalty(player.world, next_room.region)
    speed *= faction_travel_bonus(player, next_room.region)
    speed *= guild_travel_bonus(player)

    # Travel delay
    delay = max(0.5, 2.0 / speed)
    await asyncio.sleep(delay)

    await player.room.leave(player)
    await next_room.enter(player)

    await player.send(f"You travel {direction} into {next_room.name}.")

async def do_mount(player, args):
    if args not in MOUNTS:
        await player.send("No such mount.")
        return
    player.mount = MOUNTS[args].copy()
    await player.send(f"You mount your {player.mount['name']}.")

async def do_dismount(player, args):
    player.mount = None
    await player.send("You dismount.")

async def do_board(player, args):
    if args not in BOATS:
        await player.send("No such boat.")
        return
    player.boat = BOATS[args].copy()
    await player.send(f"You board the {args}.")

async def do_disembark(player, args):
    player.boat = None
    await player.send("You disembark.")

async def do_portal(player, args):
    if args not in PORTALS:
        await player.send("No such portal.")
        return

    portal = PORTALS[args]
    if player.room.vnum != portal["from"]:
        await player.send("You are not at the portal.")
        return

    # Requirements
    req = portal.get("requires", {})
    if "faction_rep" in req:
        fid, amt = req["faction_rep"]
        if player.factions.get(fid, 0) < amt:
            await player.send("The portal rejects you.")
            return

    if "item" in req:
        needed = req["item"]
        if not any(obj.vnum == needed for obj in player.inventory):
            await player.send("You lack the required item.")
            return

    dest = player.world.rooms.get(portal["to"])
    await player.room.leave(player)
    await dest.enter(player)
    await player.send("You step through the portal.")

async def do_fasttravel(player, args):
    if args not in FAST_TRAVEL_POINTS:
        await player.send("No such fast-travel point.")
        return

    if not has_fast_travel(player, args):
        await player.send("You have not unlocked that fast-travel point.")
        return

    dest_vnum = FAST_TRAVEL_POINTS[args]
    dest = player.world.rooms.get(dest_vnum)

    await player.room.leave(player)
    await dest.enter(player)
    await player.send(f"You fast-travel to {dest.name}.")

async def do_caravan(player, args):
    if args not in CARAVANS:
        await player.send("No such caravan route.")
        return

    route = CARAVANS[args]
    if player.room.vnum != route["start"]:
        await player.send("You are not at the caravan start.")
        return

    await player.send("You join the caravan...")

    # Travel time
    await asyncio.sleep(5)

    # Danger
    if random.random() < route["danger"]:
        await player.send("Bandits attack the caravan!")
        # Hook into combat system here

    # Arrive
    dest = player.world.rooms.get(route["end"])
    await player.room.leave(player)
    await dest.enter(player)

    # Rewards
    player.gold += route["reward"]["gold"]
    fid, amt = route["reward"]["rep"]
    player.factions[fid] = player.factions.get(fid, 0) + amt

    await player.send("You arrive safely with the caravan.")

COMMAND_DEFS = [
    ("north", lambda p,a: do_move(p,"north"), {"position": "standing"}),
    ("south", lambda p,a: do_move(p,"south"), {"position": "standing"}),
    ("east",  lambda p,a: do_move(p,"east"),  {"position": "standing"}),
    ("west",  lambda p,a: do_move(p,"west"),  {"position": "standing"}),

    ("mount",      do_mount,      {"position": "standing", "help_category": "travel"}),
    ("dismount",   do_dismount,   {"position": "standing", "help_category": "travel"}),
    ("board",      do_board,      {"position": "standing", "help_category": "travel"}),
    ("disembark",  do_disembark,  {"position": "standing", "help_category": "travel"}),
    ("portal",     do_portal,     {"position": "standing", "help_category": "travel"}),
    ("fasttravel", do_fasttravel, {"position": "standing", "help_category": "travel"}),
    ("caravan",    do_caravan,    {"position": "standing", "help_category": "travel"}),
]
