"""
Realms of Cyrisea - Character Creation System
Handles:
- Name validation
- Race selection
- Class selection
- Appearance customization
- Build/body type tradeoffs
- Stat rolling (3d6 or point-buy)
- Racial minimums & modifiers
- Class modifiers
- PvP mode selection
- Starting zone assignment
- Rerolling, backtracking, preview looping
"""

import asyncio
import random
from core import Player


# ---------------------------------------------------------
# Name Validation
# ---------------------------------------------------------

BLACKLIST = {
    "admin", "builder", "moderator",
    "fuck", "shit", "bitch", "cunt",
    "hitler", "nazi", "slave", "rapist",
}

def validate_name(name):
    if len(name) < 3 or len(name) > 16:
        return False, "Name must be between 3 and 16 characters."

    if not name.isalpha():
        return False, "Name must contain only letters."

    if name.lower() in BLACKLIST:
        return False, "That name is not allowed."

    return True, ""


# ---------------------------------------------------------
# Races
# ---------------------------------------------------------

RACES = {
    "human": {
        "min": {"MIG": 8, "FIN": 8, "VIT": 8, "ARC": 8, "SPI": 8, "PRE": 8},
        "mod": {"choice": 1},
        "start_zone": "sunspire",
    },
    "elf": {
        "min": {"MIG": 8, "FIN": 10, "VIT": 8, "ARC": 10, "SPI": 8, "PRE": 8},
        "mod": {"FIN": 2, "ARC": 1},
        "start_zone": "crystalwood",
    },
    "dwarf": {
        "min": {"MIG": 10, "FIN": 8, "VIT": 10, "ARC": 8, "SPI": 8, "PRE": 8},
        "mod": {"VIT": 2, "MIG": 1},
        "start_zone": "obsidian_order",
    },
    "frostborn": {
        "min": {"MIG": 8, "FIN": 8, "VIT": 12, "ARC": 8, "SPI": 10, "PRE": 8},
        "mod": {"VIT": 2, "SPI": 1},
        "start_zone": "frostpeak",
    },
}


# ---------------------------------------------------------
# Classes
# ---------------------------------------------------------

CLASSES = {
    "warrior": {
        "mod": {"MIG": 2, "VIT": 1},
        "start_items": [1001, 1002],
    },
    "ranger": {
        "mod": {"FIN": 2, "PRE": 1},
        "start_items": [1003],
    },
    "mage": {
        "mod": {"ARC": 3},
        "start_items": [1004],
    },
    "cleric": {
        "mod": {"SPI": 2, "PRE": 1},
        "start_items": [1005],
    },
}


# ---------------------------------------------------------
# Appearance Options
# ---------------------------------------------------------

SKIN_TONES = ["pale", "fair", "tan", "olive", "brown", "dark"]
HAIR_COLORS = ["black", "brown", "blonde", "red", "white", "silver"]
EYE_COLORS = ["brown", "blue", "green", "hazel", "gray", "amber"]

BUILDS = {
    "frail": {"ARC": 1, "MIG": -1},
    "average": {},
    "muscular": {"MIG": 1, "FIN": -1},
    "heavy": {"VIT": 1, "FIN": -1},
}


# ---------------------------------------------------------
# Stat Rolling
# ---------------------------------------------------------

def roll_3d6():
    return random.randint(3, 18)

def apply_minimums(stats, mins):
    for k, v in mins.items():
        if stats[k] < v:
            stats[k] = v

def apply_modifiers(stats, mods):
    for k, v in mods.items():
        if k == "choice":
            continue
        stats[k] += v


# ---------------------------------------------------------
# Character Creation Flow
# ---------------------------------------------------------

async def create_character(server, reader, writer, account):

    async def prompt(msg):
        writer.write((msg + "\n").encode())
        await writer.drain()
        data = await reader.readline()
        return data.decode().strip()

    # -----------------------------------------------------
    # Name
    # -----------------------------------------------------
    while True:
        name = await prompt("Enter character name:")
        valid, msg = validate_name(name)
        if valid:
            break
        writer.write((msg + "\n").encode())
        await writer.drain()

    # -----------------------------------------------------
    # Race
    # -----------------------------------------------------
    writer.write(b"Choose a race:\n")
    for r in RACES:
        writer.write(f" - {r}\n".encode())
    await writer.drain()

    while True:
        race = (await reader.readline()).decode().strip().lower()
        if race in RACES:
            break
        writer.write(b"Invalid race.\n")

    # -----------------------------------------------------
    # Class
    # -----------------------------------------------------
    writer.write(b"Choose a class:\n")
    for c in CLASSES:
        writer.write(f" - {c}\n".encode())
    await writer.drain()

    while True:
        class_name = (await reader.readline()).decode().strip().lower()
        if class_name in CLASSES:
            break
        writer.write(b"Invalid class.\n")

    # -----------------------------------------------------
    # Appearance (Random BEFORE preview)
    # -----------------------------------------------------
    writer.write(b"Randomize appearance? (yes/no)\n")
    await writer.drain()

    rand = (await reader.readline()).decode().strip().lower()

    if rand == "yes":
        skin = random.choice(SKIN_TONES)
        hair = random.choice(HAIR_COLORS)
        eyes = random.choice(EYE_COLORS)
        height = str(random.randint(150, 210))
        weight = str(random.randint(50, 140))
    else:
        skin = await prompt(f"Choose skin tone {SKIN_TONES}:")
        hair = await prompt(f"Choose hair color {HAIR_COLORS}:")
        eyes = await prompt(f"Choose eye color {EYE_COLORS}:")
        height = await prompt("Enter height in cm:")
        weight = await prompt("Enter weight in kg:")

    # -----------------------------------------------------
    # Recommended Builds
    # -----------------------------------------------------
    writer.write(b"\nRecommended builds:\n")
    if class_name == "warrior":
        writer.write(b" - muscular (best damage)\n")
        writer.write(b" - heavy (best tank)\n")
    elif class_name == "ranger":
        writer.write(b" - frail (best ARC synergy)\n")
        writer.write(b" - average (balanced)\n")
    elif class_name == "mage":
        writer.write(b" - frail (+ARC)\n")
    elif class_name == "cleric":
        writer.write(b" - heavy (+VIT)\n")
        writer.write(b" - average\n")
    await writer.drain()

    # -----------------------------------------------------
    # Build
    # -----------------------------------------------------
    writer.write(b"Choose body build:\n")
    for b in BUILDS:
        writer.write(f" - {b}\n".encode())
    await writer.drain()

    while True:
        build = (await reader.readline()).decode().strip().lower()
        if build in BUILDS:
            break
        writer.write(b"Invalid build.\n")

    # -----------------------------------------------------
    # Stat Rolling
    # -----------------------------------------------------
    writer.write(b"Choose stat generation method (roll/pointbuy):\n")
    method = (await reader.readline()).decode().strip().lower()

    stats = {"MIG": 0, "FIN": 0, "VIT": 0, "ARC": 0, "SPI": 0, "PRE": 0}

    if method == "roll":
        for k in stats:
            stats[k] = roll_3d6()
    else:
        points = 27
        for k in stats:
            stats[k] = 8

        writer.write(b"Point-buy: assign points.\n")
        await writer.drain()

        for k in stats:
            while True:
                writer.write(f"{k} (current {stats[k]}, points {points}): ".encode())
                await writer.drain()
                val = (await reader.readline()).decode().strip()
                if not val.isdigit():
                    continue
                val = int(val)
                cost = val - stats[k]
                if cost <= points and 8 <= val <= 15:
                    points -= cost
                    stats[k] = val
                    break

    # -----------------------------------------------------
    # Reroll Stats
    # -----------------------------------------------------
    writer.write(b"\nDo you want to reroll your stats? (yes/no)\n")
    await writer.drain()

    reroll = (await reader.readline()).decode().strip().lower()
    if reroll == "yes":
        return await create_character(server, reader, writer, account)

    # -----------------------------------------------------
    # Apply Racial/Class/Build Modifiers
    # -----------------------------------------------------
    apply_minimums(stats, RACES[race]["min"])
    apply_modifiers(stats, RACES[race]["mod"])

    if "choice" in RACES[race]["mod"]:
        writer.write(b"Choose a stat to receive +1:\n")
        for k in stats:
            writer.write(f" - {k}\n".encode())
        await writer.drain()

        while True:
            choice = (await reader.readline()).decode().strip().upper()
            if choice in stats:
                stats[choice] += 1
                break
            writer.write(b"Invalid stat.\n")

    apply_modifiers(stats, CLASSES[class_name]["mod"])
    apply_modifiers(stats, BUILDS[build])

    # -----------------------------------------------------
    # PvP Mode
    # -----------------------------------------------------
    writer.write(b"Choose PvP mode (peaceful/deadly):\n")
    await writer.drain()

    while True:
        mode = (await reader.readline()).decode().strip().lower()
        if mode in ("peaceful", "deadly"):
            break
        writer.write(b"Invalid mode.\n")

    # -----------------------------------------------------
    # Change Race/Class/Build Option
    # -----------------------------------------------------
    writer.write(b"\nWould you like to change race, class, or build? (yes/no)\n")
    await writer.drain()

    change = (await reader.readline()).decode().strip().lower()
    if change == "yes":
        return await create_character(server, reader, writer, account)

    # -----------------------------------------------------
    # Preview Screen
    # -----------------------------------------------------
    writer.write(b"\n===== CHARACTER PREVIEW =====\n")
    writer.write(f"Name: {name}\n".encode())
    writer.write(f"Race: {race}\n".encode())
    writer.write(f"Class: {class_name}\n".encode())
    writer.write(f"PvP Mode: {'Peaceful' if mode == 'peaceful' else 'Deadly'}\n".encode())

    writer.write(b"\nAppearance:\n")
    writer.write(f"  Skin: {skin}\n".encode())
    writer.write(f"  Hair: {hair}\n".encode())
    writer.write(f"  Eyes: {eyes}\n".encode())
    writer.write(f"  Height: {height} cm\n".encode())
    writer.write(f"  Weight: {weight} kg\n".encode())
    writer.write(f"  Build: {build}\n".encode())

    writer.write(b"\nStats:\n")
    for k, v in stats.items():
        writer.write(f"  {k}: {v}\n".encode())

    writer.write(b"\nStarting Zone: ".encode())
    writer.write(f"{RACES[race]['start_zone']}\n".encode())

    writer.write(b"\nConfirm character? (yes/no/preview)\n")
    await writer.drain()

    confirm = (await reader.readline()).decode().strip().lower()

    if confirm == "preview":
        return await create_character(server, reader, writer, account)

    if confirm != "yes":
        writer.write(b"Character creation cancelled.\n")
        await writer.drain()
        return None

    # -----------------------------------------------------
    # Create Player Object
    # -----------------------------------------------------
    player = Player(name=name, world=server.world)
    player.race = race
    player.class_name = class_name
    player.stats.update(stats)

    player.appearance = {
        "skin": skin,
        "hair": hair,
        "eyes": eyes,
        "height": height,
        "weight": weight,
        "build": build,
    }

    player.is_peaceful = (mode == "peaceful")
    player.is_deadly = (mode == "deadly")

    # Starting zone
    start_zone = RACES[race]["start_zone"]
    for room in server.world.rooms.values():
        if room.region == start_zone:
            await room.enter(player)
            break

    # Starting items
    for vnum in CLASSES[class_name]["start_items"]:
        if vnum in server.world.objects:
            player.inventory.append(server.world.objects[vnum].clone())

    # Save character
    from accounts import save_character, save_account
    account.characters.append(name)
    save_account(account)
    save_character(player)

    writer.write(b"Character creation complete!\n")
    await writer.drain()

    return player
