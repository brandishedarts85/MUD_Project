"""
Realms of Cyrisea - Event System
Full event suite:
- World events
- Invasions
- Festivals
- Seasonal events
- Faction events
- Dynamic triggers
- Event rewards
"""

import asyncio
import random
import logging


# ---------------------------------------------------------
# Event registry
# ---------------------------------------------------------

EVENTS = {
    "forest_invasion": {
        "name": "Invasion of the Crystalwood",
        "type": "invasion",
        "region": "crystalwood",
        "desc": "Shadow creatures spill from the Whispering Caverns.",
        "mobs": [9001, 9002, 9003],
        "duration": 300,  # seconds
        "reward": {"xp": 150, "gold": 50},
    },

    "obsidian_festival": {
        "name": "Festival of the Obsidian Order",
        "type": "festival",
        "region": "obsidian_order",
        "desc": "Arcane scholars gather for rites and demonstrations.",
        "effects": {"mana_regen": 2.0},
        "duration": 600,
        "reward": {"item": 7005},
    },

    "winter_storm": {
        "name": "Frostpeak Winterstorm",
        "type": "seasonal",
        "region": "frostpeak",
        "desc": "A massive blizzard sweeps across the mountains.",
        "effects": {"movement_mod": 0.6},
        "duration": 400,
        "reward": {"xp": 100},
    },

    "faction_ritual": {
        "name": "Crystalwood Heartwood Ritual",
        "type": "faction",
        "faction": "crystalwood",
        "region": "crystalwood",
        "desc": "Wardens gather to strengthen the Heartwood.",
        "effects": {"combat_mod": 1.2},
        "duration": 500,
        "reward": {"rep": 100},
    },

    "world_boss": {
        "name": "The Obsidian Colossus",
        "type": "world_boss",
        "region": "obsidian_order",
        "desc": "A towering construct awakens from ancient slumber.",
        "boss_vnum": 9500,
        "duration": 900,
        "reward": {"item": 8001, "xp": 500},
    },
}

# ---------------------------------------------------------
# Active events
# ---------------------------------------------------------

def get_active_events(world):
    return world.active_events

def start_event(world, event_id):
    event = EVENTS[event_id]
    world.active_events[event_id] = {
        "id": event_id,
        "remaining": event["duration"],
        "data": event,
    }

def end_event(world, event_id):
    if event_id in world.active_events:
        del world.active_events[event_id]

# ---------------------------------------------------------
# Event tick
# ---------------------------------------------------------

async def event_tick(world):
    """Called by server.event_task every 30 seconds."""

    # Decrement timers
    for event_id in list(world.active_events.keys()):
        world.active_events[event_id]["remaining"] -= 30

        if world.active_events[event_id]["remaining"] <= 0:
            await conclude_event(world, event_id)
            end_event(world, event_id)

    # Random chance to start events
    if random.random() < 0.05:  # 5% chance every tick
        event_id = random.choice(list(EVENTS.keys()))
        await trigger_event(world, event_id)

# ---------------------------------------------------------
# Trigger event
# ---------------------------------------------------------

async def trigger_event(world, event_id):
    event = EVENTS[event_id]
    start_event(world, event_id)

    # Notify players in region
    for p in world.players:
        if getattr(p.room, "region", None) == event["region"]:
            await p.send(f"\033[95mEvent Started:\033[0m {event['name']}")
            await p.send(event["desc"])

    # Spawn mobs for invasions
    if event["type"] == "invasion":
        for vnum in event["mobs"]:
            mob_template = world.mobs.get(vnum)
            if mob_template:
                mob = mob_template.clone()
                region_rooms = [
                    r for r in world.rooms.values()
                    if getattr(r, "region", None) == event["region"]
                ]
                if region_rooms:
                    mob.spawn(random.choice(region_rooms))

    # Spawn world boss
    if event["type"] == "world_boss":
        boss_template = world.mobs.get(event["boss_vnum"])
        if boss_template:
            boss = boss_template.clone()
            region_rooms = [
                r for r in world.rooms.values()
                if getattr(r, "region", None) == event["region"]
            ]
            if region_rooms:
                boss.spawn(random.choice(region_rooms))

# ---------------------------------------------------------
# Conclude event
# ---------------------------------------------------------

async def conclude_event(world, event_id):
    event = EVENTS[event_id]

    for p in world.players:
        if getattr(p.room, "region", None) == event["region"]:
            await p.send(f"\033[94mEvent Concluded:\033[0m {event['name']}")

            reward = event.get("reward", {})

            # XP reward
            if "xp" in reward:
                p.exp += reward["xp"]
                await p.send(f"You gain {reward['xp']} XP.")

            # Gold reward
            if "gold" in reward:
                p.gold += reward["gold"]
                await p.send(f"You gain {reward['gold']} gold.")

            # Item reward
            if "item" in reward:
                obj = world.objects.get(reward["item"])
                if obj:
                    p.inventory.append(obj)
                    await p.send(f"You receive: {obj.short_desc}")

            # Faction reputation
            if "rep" in reward:
                fid = event.get("faction")
                if fid:
                    p.factions[fid] = p.factions.get(fid, 0) + reward["rep"]
                    await p.send(f"You gain {reward['rep']} reputation with {fid}.")

# ---------------------------------------------------------
# Show active events
# ---------------------------------------------------------

async def do_events(player, args):
    world = player.world
    active = get_active_events(world)

    if not active:
        await player.send("No active events.")
        return

    await player.send("\033[95mActive Events:\033[0m")

    for eid, data in active.items():
        event = data["data"]
        remaining = data["remaining"]

        await player.send(f"{event['name']} — {remaining}s remaining")

# ---------------------------------------------------------
# Show event details
# ---------------------------------------------------------

async def do_event(player, args):
    if not args:
        await player.send("Event which?")
        return

    if args.lower() not in EVENTS:
        await player.send("No such event.")
        return

    event = EVENTS[args.lower()]

    await player.send(f"\033[94mEvent: {event['name']}\033[0m")
    await player.send(event["desc"])
    await player.send(f"Type: {event['type']}")
    await player.send(f"Region: {event['region']}")
    await player.send(f"Duration: {event['duration']}s")

COMMAND_DEFS = [
    ("events", do_events, {"position": "standing", "help_category": "events"}),
    ("event",  do_event,  {"position": "standing", "help_category": "events"}),
]
