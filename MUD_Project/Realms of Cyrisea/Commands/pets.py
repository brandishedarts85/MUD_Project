"""
Realms of Cyrisea - Pet System
Full pet suite:
- Combat pets
- Cosmetic pets
- Pet leveling
- Pet abilities
- Pet bonding
- Feeding & happiness
- Breeding
- Rarity tiers
"""

import asyncio
import random
import logging

# ---------------------------------------------------------
# Rarity tiers
# ---------------------------------------------------------

RARITY_TIERS = {
    "common": 1.0,
    "uncommon": 1.1,
    "rare": 1.25,
    "epic": 1.5,
    "legendary": 2.0,
}

# ---------------------------------------------------------
# Pet registry
# ---------------------------------------------------------

PETS = {
    "forest_sprite": {
        "name": "Forest Sprite",
        "rarity": "uncommon",
        "desc": "A tiny glowing spirit of the woods.",
        "combat": True,
        "base_hp": 50,
        "base_attack": 8,
        "abilities": ["nature_bolt"],
        "food": ["berries", "herbs"],
    },
    "ember_pup": {
        "name": "Ember Pup",
        "rarity": "rare",
        "desc": "A fiery little hound with ember eyes.",
        "combat": True,
        "base_hp": 70,
        "base_attack": 10,
        "abilities": ["ember_bite"],
        "food": ["meat"],
    },
    "sky_moth": {
        "name": "Sky Moth",
        "rarity": "common",
        "desc": "A gentle moth with shimmering wings.",
        "combat": False,
        "base_hp": 20,
        "base_attack": 0,
        "abilities": [],
        "food": ["nectar"],
    },
    "obsidian_imp": {
        "name": "Obsidian Imp",
        "rarity": "epic",
        "desc": "A mischievous imp born of arcane storms.",
        "combat": True,
        "base_hp": 90,
        "base_attack": 14,
        "abilities": ["shadow_bolt", "arcane_pop"],
        "food": ["mana_crystal"],
    },
}

# ---------------------------------------------------------
# Pet abilities
# ---------------------------------------------------------

PET_ABILITIES = {
    "nature_bolt": {
        "dtype": "poison",
        "power": 1.0,
        "desc": "A bolt of natural energy.",
    },
    "ember_bite": {
        "dtype": "fire",
        "power": 1.2,
        "desc": "A fiery bite.",
    },
    "shadow_bolt": {
        "dtype": "arcane",
        "power": 1.3,
        "desc": "A bolt of shadow energy.",
    },
    "arcane_pop": {
        "dtype": "arcane",
        "power": 1.0,
        "desc": "A disruptive arcane burst.",
    },
}

# ---------------------------------------------------------
# Player pet state
# ---------------------------------------------------------

def get_pet(player):
    return getattr(player, "pet", None)

def create_pet_instance(player, pet_id):
    template = PETS[pet_id]
    rarity_mod = RARITY_TIERS[template["rarity"]]

    return {
        "id": pet_id,
        "name": template["name"],
        "rarity": template["rarity"],
        "level": 1,
        "xp": 0,
        "hp": int(template["base_hp"] * rarity_mod),
        "max_hp": int(template["base_hp"] * rarity_mod),
        "attack": int(template["base_attack"] * rarity_mod),
        "abilities": template["abilities"],
        "combat": template["combat"],
        "happiness": 100,
        "bond": 0,
        "food": template["food"],
    }

# ---------------------------------------------------------
# Summon pet
# ---------------------------------------------------------

async def do_pet(player, args):
    """Summon or dismiss your pet."""

    if not args:
        await player.send("Syntax: pet <summon/dismiss>")
        return

    if args == "summon":
        if not player.pet_data:
            await player.send("You do not have a pet.")
            return

        player.pet = player.pet_data
        await player.send(f"You summon your {player.pet['name']}.")
        return

    if args == "dismiss":
        player.pet = None
        await player.send("You dismiss your pet.")
        return

    await player.send("Use summon/dismiss.")

# ---------------------------------------------------------
# Acquire pet
# ---------------------------------------------------------

async def do_petget(player, args):
    """Acquire a pet."""

    if args.lower() not in PETS:
        await player.send("No such pet.")
        return

    if player.pet_data:
        await player.send("You already have a pet.")
        return

    pet = create_pet_instance(player, args.lower())
    player.pet_data = pet

    await player.send(f"You bond with a {pet['name']}!")

# ---------------------------------------------------------
# Feed pet
# ---------------------------------------------------------

async def do_feed(player, args):
    """Feed your pet."""

    pet = get_pet(player)
    if not pet:
        await player.send("Your pet is not summoned.")
        return

    item_name = args.lower()

    for obj in list(player.inventory):
        if item_name in obj.short_desc.lower() and obj.food_type in pet["food"]:
            player.inventory.remove(obj)
            pet["happiness"] = min(100, pet["happiness"] + 20)
            pet["bond"] += 5
            await player.send(f"You feed your {pet['name']}. Happiness increases.")
            return

    await player.send("Your pet will not eat that.")

# ---------------------------------------------------------
# Pet leveling
# ---------------------------------------------------------

def pet_gain_xp(pet, amount):
    pet["xp"] += amount
    if pet["xp"] >= pet["level"] * 50:
        pet["xp"] = 0
        pet["level"] += 1
        pet["max_hp"] += 10
        pet["attack"] += 2
        pet["hp"] = pet["max_hp"]

# ---------------------------------------------------------
# Pet combat
# ---------------------------------------------------------

async def pet_combat_round(player, pet, target):
    """Pet attacks target."""

    if not pet["combat"]:
        return

    ability_id = random.choice(pet["abilities"])
    ability = PET_ABILITIES[ability_id]

    dmg = int(pet["attack"] * ability["power"])
    target.hp -= dmg

    await player.send(f"Your {pet['name']} uses {ability_id.replace('_',' ')} for {dmg} damage!")
    await target.send(f"{player.pet['name']} hits you for {dmg} damage!")

    if target.hp <= 0:
        await kill_target(player, target)
        pet_gain_xp(pet, 20)

# ---------------------------------------------------------
# Pet commands
# ---------------------------------------------------------

async def do_petcmd(player, args):
    """Command your pet."""

    pet = get_pet(player)
    if not pet:
        await player.send("Your pet is not summoned.")
        return

    if args == "stay":
        pet["stay"] = True
        await player.send(f"Your {pet['name']} stays.")
        return

    if args == "follow":
        pet["stay"] = False
        await player.send(f"Your {pet['name']} follows you.")
        return

    await player.send("Commands: stay, follow")

# ---------------------------------------------------------
# Pet breeding
# ---------------------------------------------------------

async def do_breed(player, args):
    """Breed two pets."""

    if not player.breeding_slot:
        await player.send("You have no breeding slot.")
        return

    parts = args.split()
    if len(parts) != 2:
        await player.send("Syntax: breed <pet1> <pet2>")
        return

    p1, p2 = parts

    if p1 not in PETS or p2 not in PETS:
        await player.send("Invalid pets.")
        return

    # Simple breeding logic
    rarity1 = RARITY_TIERS[PETS[p1]["rarity"]]
    rarity2 = RARITY_TIERS[PETS[p2]["rarity"]]

    if random.random() < (rarity1 + rarity2) / 4:
        baby_id = random.choice([p1, p2])
    else:
        baby_id = "forest_sprite"  # fallback common pet

    baby = create_pet_instance(player, baby_id)
    player.pet_data = baby

    await player.send(f"A new pet is born: {baby['name']}!")

COMMAND_DEFS = [
    ("pet",     do_pet,     {"position": "standing", "help_category": "pets"}),
    ("petget",  do_petget,  {"position": "standing", "help_category": "pets"}),
    ("feed",    do_feed,    {"position": "standing", "help_category": "pets"}),
    ("petcmd",  do_petcmd,  {"position": "standing", "help_category": "pets"}),
    ("breed",   do_breed,   {"position": "standing", "help_category": "pets"}),
]
