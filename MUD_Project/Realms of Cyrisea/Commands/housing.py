"""
Realms of Cyrisea - Housing System
Full housing suite:
- Instanced player housing
- Furniture placement
- Storage containers
- Crafting stations
- Gardens
- Housing upgrades
- Permissions
- Housing districts
"""

import asyncio
import logging
import random

# ---------------------------------------------------------
# Housing registry
# ---------------------------------------------------------

HOUSING_TEMPLATES = {
    "basic_home": {
        "name": "Basic Home",
        "rooms": ["living_room", "bedroom", "storage"],
        "cost": 500,
        "desc": "A modest but cozy home.",
    },
    "forest_cabin": {
        "name": "Forest Cabin",
        "rooms": ["main_hall", "bedroom", "garden"],
        "cost": 1200,
        "desc": "A wooden cabin nestled in the forest.",
    },
    "arcane_study": {
        "name": "Arcane Study",
        "rooms": ["library", "laboratory", "vault"],
        "cost": 2000,
        "desc": "A magical residence for arcane scholars.",
    },
}

# ---------------------------------------------------------
# Player housing state
# ---------------------------------------------------------

def has_home(player):
    return player.home is not None

def create_home_instance(world, template_id, owner):
    """Create an instanced housing area for the player."""

    template = HOUSING_TEMPLATES[template_id]
    instance = {}

    base_vnum = world.next_instance_vnum
    world.next_instance_vnum += 100  # reserve block

    for i, room_name in enumerate(template["rooms"]):
        vnum = base_vnum + i
        room = world.create_room(vnum, f"{template['name']} - {room_name}", "")
        room.owner = owner.name
        room.is_housing = True
        room.furniture = []
        room.storage = []
        room.stations = []
        room.garden = []
        instance[room_name] = room

    # Connect rooms linearly
    names = template["rooms"]
    for i in range(len(names) - 1):
        r1 = instance[names[i]]
        r2 = instance[names[i + 1]]
        r1.add_exit("east", r2)
        r2.add_exit("west", r1)

    return instance

# ---------------------------------------------------------
# Buy housing
# ---------------------------------------------------------

async def do_buyhome(player, args):
    """Purchase a home."""

    if has_home(player):
        await player.send("You already own a home.")
        return

    if args.lower() not in HOUSING_TEMPLATES:
        await player.send("No such housing type.")
        return

    template = HOUSING_TEMPLATES[args.lower()]

    if player.gold < template["cost"]:
        await player.send("You cannot afford that home.")
        return

    player.gold -= template["cost"]

    instance = create_home_instance(player.world, args.lower(), player)
    player.home = instance

    await player.send(f"You purchase a {template['name']}!")
    await player.send("Use 'home' to enter your residence.")

# ---------------------------------------------------------
# Enter home
# ---------------------------------------------------------

async def do_home(player, args):
    """Enter your home."""

    if not has_home(player):
        await player.send("You do not own a home.")
        return

    living_room = player.home[list(player.home.keys())[0]]

    await player.room.leave(player)
    await living_room.enter(player)

    await player.send("You enter your home.")

# ---------------------------------------------------------
# Furniture placement
# ---------------------------------------------------------

async def do_place(player, args):
    """Place furniture in your home."""

    if not player.room.is_housing or player.room.owner != player.name:
        await player.send("You can only place furniture in your own home.")
        return

    item_name = args.lower()

    for obj in list(player.inventory):
        if item_name in obj.short_desc.lower() and obj.is_furniture:
            player.inventory.remove(obj)
            player.room.furniture.append(obj)
            await player.send(f"You place {obj.short_desc}.")
            return

    await player.send("You do not have that furniture item.")

# ---------------------------------------------------------
# Storage
# ---------------------------------------------------------

async def do_store(player, args):
    """Store an item in your home."""

    if not player.room.is_housing or player.room.owner != player.name:
        await player.send("You can only store items in your own home.")
        return

    item_name = args.lower()

    for obj in list(player.inventory):
        if item_name in obj.short_desc.lower():
            player.inventory.remove(obj)
            player.room.storage.append(obj)
            await player.send(f"You store {obj.short_desc}.")
            return

    await player.send("You do not have that item.")

async def do_retrieve(player, args):
    """Retrieve an item from home storage."""

    if not player.room.is_housing or player.room.owner != player.name:
        await player.send("You can only retrieve items in your own home.")
        return

    item_name = args.lower()

    for obj in list(player.room.storage):
        if item_name in obj.short_desc.lower():
            player.room.storage.remove(obj)
            player.inventory.append(obj)
            await player.send(f"You retrieve {obj.short_desc}.")
            return

    await player.send("No such item in storage.")

# ---------------------------------------------------------
# Crafting stations
# ---------------------------------------------------------

async def do_install(player, args):
    """Install a crafting station in your home."""

    if not player.room.is_housing or player.room.owner != player.name:
        await player.send("You can only install stations in your own home.")
        return

    station_name = args.lower()

    for obj in list(player.inventory):
        if obj.is_station and station_name in obj.short_desc.lower():
            player.inventory.remove(obj)
            player.room.stations.append(obj.station_type)
            await player.send(f"You install a {obj.short_desc}.")
            return

    await player.send("You do not have that station.")

# ---------------------------------------------------------
# Gardens
# ---------------------------------------------------------

async def do_plant(player, args):
    """Plant seeds in your home garden."""

    if not player.room.is_housing or player.room.owner != player.name:
        await player.send("You can only plant in your own home.")
        return

    if not hasattr(player.room, "garden"):
        await player.send("This room has no garden.")
        return

    seed_name = args.lower()

    for obj in list(player.inventory):
        if obj.is_seed and seed_name in obj.short_desc.lower():
            player.inventory.remove(obj)
            player.room.garden.append({"seed": obj, "growth": 0})
            await player.send(f"You plant {obj.short_desc}.")
            return

    await player.send("You do not have that seed.")

async def housing_tick(world):
    """Grow plants in player gardens."""

    for p in world.players:
        if not has_home(p):
            continue

        for room in p.home.values():
            for plant in room.garden:
                plant["growth"] += 1
                if plant["growth"] == 5:
                    plant["ready"] = True

async def do_harvest(player, args):
    """Harvest grown plants."""

    if not player.room.is_housing or player.room.owner != player.name:
        await player.send("You can only harvest in your own home.")
        return

    harvested = 0

    for plant in list(player.room.garden):
        if plant.get("ready"):
            result = plant["seed"].harvest_result
            obj = player.world.objects.get(result)
            if obj:
                player.inventory.append(obj.clone())
            player.room.garden.remove(plant)
            harvested += 1

    if harvested:
        await player.send(f"You harvest {harvested} plants.")
    else:
        await player.send("Nothing is ready to harvest.")

# ---------------------------------------------------------
# Housing permissions
# ---------------------------------------------------------

async def do_homeperm(player, args):
    """Manage home permissions."""

    if not has_home(player):
        await player.send("You do not own a home.")
        return

    parts = args.split()
    if len(parts) != 2:
        await player.send("Syntax: homeperm <add/remove> <player>")
        return

    action, name = parts
    name = name.lower()

    if action == "add":
        player.home_perms.add(name)
        await player.send(f"{name} can now enter your home.")
    elif action == "remove":
        player.home_perms.discard(name)
        await player.send(f"{name} can no longer enter your home.")
    else:
        await player.send("Use add/remove.")

COMMAND_DEFS = [
    ("buyhome",   do_buyhome,   {"position": "standing", "help_category": "housing"}),
    ("home",      do_home,      {"position": "standing", "help_category": "housing"}),
    ("place",     do_place,     {"position": "standing", "help_category": "housing"}),
    ("store",     do_store,     {"position": "standing", "help_category": "housing"}),
    ("retrieve",  do_retrieve,  {"position": "standing", "help_category": "housing"}),
    ("install",   do_install,   {"position": "standing", "help_category": "housing"}),
    ("plant",     do_plant,     {"position": "standing", "help_category": "housing"}),
    ("harvest",   do_harvest,   {"position": "standing", "help_category": "housing"}),
    ("homeperm",  do_homeperm,  {"position": "standing", "help_category": "housing"}),
]
