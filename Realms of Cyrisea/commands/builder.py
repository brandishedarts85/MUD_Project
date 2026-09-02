"""
Realms of Cyrisea - Builder & Admin Tools
Full builder suite:
- Room creation & editing
- Exit creation & editing
- Mob creation & editing
- Object creation & editing
- Area saving & loading
- Zone resets
- Builder permissions
- Live reload
- Logging hooks
- Batch creation tools
"""

import asyncio
import logging
import json
import random

log = logging.getLogger(__name__)

# ---------------------------------------------------------
# Builder permissions
# ---------------------------------------------------------

def is_builder(player):
    return getattr(player, "is_builder", False) or getattr(player, "is_admin", False)

# ---------------------------------------------------------
# Room creation
# ---------------------------------------------------------

async def do_rcreate(player, args):
    if not is_builder(player):
        await player.send("You do not have builder permissions.")
        return

    parts = args.split(" ", 1)
    if len(parts) != 2:
        await player.send("Syntax: rcreate <vnum> <name>")
        return

    vnum = int(parts[0])
    name = parts[1]

    if vnum in player.world.rooms:
        await player.send("A room with that vnum already exists.")
        return

    room = player.world.create_room(vnum, name, "")
    await player.send(f"Room {vnum} created: {name}")

async def do_rdesc(player, args):
    if not is_builder(player):
        await player.send("You do not have builder permissions.")
        return

    player.room.desc = args
    await player.send("Room description updated.")

async def do_rterrain(player, args):
    if not is_builder(player):
        await player.send("You do not have builder permissions.")
        return

    player.room.terrain = args
    await player.send(f"Room terrain set to {args}.")

# ---------------------------------------------------------
# Exit creation
# ---------------------------------------------------------

async def do_rexit(player, args):
    if not is_builder(player):
        await player.send("You do not have builder permissions.")
        return

    parts = args.split()
    if len(parts) != 2:
        await player.send("Syntax: rexit <direction> <vnum>")
        return

    direction, vnum = parts
    vnum = int(vnum)

    if vnum not in player.world.rooms:
        await player.send("No such room.")
        return

    player.room.add_exit(direction, player.world.rooms[vnum])
    await player.send(f"Exit {direction} -> {vnum} created.")

# ---------------------------------------------------------
# Mob creation
# ---------------------------------------------------------

async def do_mcreate(player, args):
    if not is_builder(player):
        await player.send("You do not have builder permissions.")
        return

    parts = args.split(" ", 1)
    if len(parts) != 2:
        await player.send("Syntax: mcreate <vnum> <name>")
        return

    vnum = int(parts[0])
    name = parts[1]

    if vnum in player.world.mobs:
        await player.send("A mob with that vnum already exists.")
        return

    mob = player.world.create_mob(vnum, name)
    mob.room = player.room
    player.room.mobs.append(mob)

    await player.send(f"Mob {vnum} created: {name}")

async def do_mdesc(player, args):
    if not is_builder(player):
        await player.send("You do not have builder permissions.")
        return

    mob = player.room.find_mob(args)
    if not mob:
        await player.send("Mob not found.")
        return

    mob.desc = args
    await player.send("Mob description updated.")

# ---------------------------------------------------------
# Object creation
# ---------------------------------------------------------

async def do_ocreate(player, args):
    if not is_builder(player):
        await player.send("You do not have builder permissions.")
        return

    parts = args.split(" ", 1)
    if len(parts) != 2:
        await player.send("Syntax: ocreate <vnum> <name>")
        return

    vnum = int(parts[0])
    name = parts[1]

    if vnum in player.world.objects:
        await player.send("An object with that vnum already exists.")
        return

    obj = player.world.create_object(vnum, name)
    player.room.objects.append(obj)

    await player.send(f"Object {vnum} created: {name}")

async def do_odesc(player, args):
    if not is_builder(player):
        await player.send("You do not have builder permissions.")
        return

    obj = player.room.find_object(args)
    if not obj:
        await player.send("Object not found.")
        return

    obj.desc = args
    await player.send("Object description updated.")

# ---------------------------------------------------------
# Area saving
# ---------------------------------------------------------

async def do_asave(player, args):
    if not is_builder(player):
        await player.send("You do not have builder permissions.")
        return

    area_name = args or "default_area"
    data = {
        "rooms": {},
        "mobs": {},
        "objects": {},
    }

    for vnum, room in player.world.rooms.items():
        data["rooms"][vnum] = {
            "name": room.name,
            "desc": room.desc,
            "terrain": getattr(room, "terrain", "road"),
            "exits": {d: r.vnum for d, r in room.exits.items()},
        }

    for vnum, mob in player.world.mobs.items():
        data["mobs"][vnum] = {
            "name": mob.name,
            "desc": mob.desc,
            "level": mob.level,
        }

    for vnum, obj in player.world.objects.items():
        data["objects"][vnum] = {
            "name": obj.short_desc,
            "desc": obj.desc,
            "stats": getattr(obj, "stats", {}),
        }

    with open(f"areas/{area_name}.json", "w") as f:
        json.dump(data, f, indent=2)

    await player.send(f"Area saved to areas/{area_name}.json")

async def do_aload(player, args):
    if not is_builder(player):
        await player.send("You do not have builder permissions.")
        return

    area_name = args or "default_area"

    try:
        with open(f"areas/{area_name}.json") as f:
            data = json.load(f)
    except:
        await player.send("Area file not found.")
        return

    # Load rooms
    for vnum, rdata in data["rooms"].items():
        room = player.world.create_room(vnum, rdata["name"], rdata["desc"])
        room.terrain = rdata.get("terrain", "road")

    # Load exits
    for vnum, rdata in data["rooms"].items():
        room = player.world.rooms[vnum]
        for d, rv in rdata["exits"].items():
            if rv in player.world.rooms:
                room.add_exit(d, player.world.rooms[rv])

    # Load mobs
    for vnum, mdata in data["mobs"].items():
        mob = player.world.create_mob(vnum, mdata["name"])
        mob.desc = mdata["desc"]
        mob.level = mdata["level"]

    # Load objects
    for vnum, odata in data["objects"].items():
        obj = player.world.create_object(vnum, odata["name"])
        obj.desc = odata["desc"]
        obj.stats = odata.get("stats", {})

    await player.send(f"Area {area_name} loaded.")

# ---------------------------------------------------------
# Zone resets
# ---------------------------------------------------------

async def do_zreset(player, args):
    if not is_builder(player):
        await player.send("You do not have builder permissions.")
        return

    for room in player.world.rooms.values():
        # Respawn mobs
        for mob in list(room.mobs):
            if mob.respawn:
                new_mob = player.world.create_mob(mob.vnum, mob.name)
                room.mobs.append(new_mob)

        # Respawn objects
        for obj in list(room.objects):
            if getattr(obj, "respawn", False):
                new_obj = player.world.create_object(obj.vnum, obj.short_desc)
                room.objects.append(new_obj)

    await player.send("Zone reset complete.")

# ---------------------------------------------------------
# Live reload
# ---------------------------------------------------------

async def do_reload(player, args):
    if not player.is_admin:
        await player.send("Only admins may reload modules.")
        return

    await player.send("Reloading world modules...")
    player.world.reload_modules()
    await player.send("Reload complete.")

# ---------------------------------------------------------
# Batch creation
# ---------------------------------------------------------

async def do_rbatch(player, args):
    if not is_builder(player):
        await player.send("You do not have builder permissions.")
        return

    parts = args.split()
    if len(parts) != 3:
        await player.send("Syntax: rbatch <start_vnum> <count> <basename>")
        return

    start, count, basename = int(parts[0]), int(parts[1]), parts[2]

    for i in range(count):
        vnum = start + i
        name = f"{basename} {i+1}"
        player.world.create_room(vnum, name, "")
    await player.send(f"{count} rooms created starting at {start}.")

COMMAND_DEFS = [
    ("rcreate",  do_rcreate,  {"position": "standing", "help_category": "builder"}),
    ("rdesc",    do_rdesc,    {"position": "standing", "help_category": "builder"}),
    ("rterrain", do_rterrain, {"position": "standing", "help_category": "builder"}),
    ("rexit",    do_rexit,    {"position": "standing", "help_category": "builder"}),

    ("mcreate",  do_mcreate,  {"position": "standing", "help_category": "builder"}),
    ("mdesc",    do_mdesc,    {"position": "standing", "help_category": "builder"}),

    ("ocreate",  do_ocreate,  {"position": "standing", "help_category": "builder"}),
    ("odesc",    do_odesc,    {"position": "standing", "help_category": "builder"}),

    ("asave",    do_asave,    {"position": "standing", "help_category": "builder"}),
    ("aload",    do_aload,    {"position": "standing", "help_category": "builder"}),

    ("zreset",   do_zreset,   {"position": "standing", "help_category": "builder"}),
    ("reload",   do_reload,   {"position": "standing", "help_category": "builder"}),

    ("rbatch",   do_rbatch,   {"position": "standing", "help_category": "builder"}),
]
