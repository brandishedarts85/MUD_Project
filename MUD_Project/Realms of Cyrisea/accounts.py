"""
Realms of Cyrisea - Account System
Handles:
- Account creation
- Login
- Password hashing
- Character list
- Character creation entry point
- Character loading & saving
"""

import asyncio
import json
import os
import hashlib
from core import Player


ACCOUNTS_DIR = "accounts"
CHARACTERS_DIR = "characters"

os.makedirs(ACCOUNTS_DIR, exist_ok=True)
os.makedirs(CHARACTERS_DIR, exist_ok=True)


# ---------------------------------------------------------
# Password Hashing
# ---------------------------------------------------------

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# ---------------------------------------------------------
# Account Structure
# ---------------------------------------------------------

class Account:
    def __init__(self, username, password_hash, characters=None):
        self.username = username
        self.password_hash = password_hash
        self.characters = characters or []  # list of character names

    def to_dict(self):
        return {
            "username": self.username,
            "password_hash": self.password_hash,
            "characters": self.characters,
        }

    @staticmethod
    def from_dict(data):
        return Account(
            username=data["username"],
            password_hash=data["password_hash"],
            characters=data.get("characters", []),
        )


# ---------------------------------------------------------
# Account File Handling
# ---------------------------------------------------------

def account_path(username):
    return os.path.join(ACCOUNTS_DIR, f"{username.lower()}.json")


def load_account(username):
    path = account_path(username)
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        data = json.load(f)
    return Account.from_dict(data)


def save_account(account):
    path = account_path(account.username)
    with open(path, "w") as f:
        json.dump(account.to_dict(), f, indent=2)


# ---------------------------------------------------------
# Character File Handling
# ---------------------------------------------------------

def character_path(name):
    return os.path.join(CHARACTERS_DIR, f"{name.lower()}.json")


def save_character(player):
    """Save player data to JSON."""
    data = {
        "name": player.name,
        "race": getattr(player, "race", None),
        "class": getattr(player, "class_name", None),
        "appearance": getattr(player, "appearance", {}),
        "stats": player.stats,
        "inventory": [obj.vnum for obj in player.inventory],
        "gold": player.gold,
        "exp": player.exp,
        "favor": player.favor,
        "is_peaceful": player.is_peaceful,
        "is_deadly": player.is_deadly,
        "durability_penalty": player.durability_penalty,
        "fatigue": player.fatigue,
        "last_death_time": player.last_death_time,
        "last_corpse": None,  # corpses are world objects, not saved
        "location": player.room.vnum if player.room else None,
    }

    with open(character_path(player.name), "w") as f:
        json.dump(data, f, indent=2)


def load_character(world, name):
    """Load character JSON and return a Player object."""
    path = character_path(name)
    if not os.path.exists(path):
        return None

    with open(path, "r") as f:
        data = json.load(f)

    player = Player(name=data["name"], world=world)

    # Basic fields
    player.stats = data.get("stats", {})
    player.gold = data.get("gold", 0)
    player.exp = data.get("exp", 0)
    player.favor = data.get("favor", 0)
    player.is_peaceful = data.get("is_peaceful", True)
    player.is_deadly = data.get("is_deadly", False)
    player.durability_penalty = data.get("durability_penalty", 0)
    player.fatigue = data.get("fatigue", 0)
    player.last_death_time = data.get("last_death_time", None)

    # Appearance
    player.appearance = data.get("appearance", {})

    # Inventory (load objects by vnum)
    inv_vnums = data.get("inventory", [])
    for vnum in inv_vnums:
        if vnum in world.objects:
            player.inventory.append(world.objects[vnum].clone())

    # Location
    loc = data.get("location")
    if loc and loc in world.rooms:
        player.room = world.rooms[loc]
        world.rooms[loc].players.append(player)

    return player


# ---------------------------------------------------------
# Account Login Flow
# ---------------------------------------------------------

async def login_flow(server, reader, writer):
    """Handles login or account creation."""

    async def prompt(msg):
        writer.write((msg + "\n").encode())
        await writer.drain()
        data = await reader.readline()
        return data.decode().strip()

    writer.write(b"Welcome to Realms of Cyrisea!\n")
    writer.write(b"Do you have an account? (yes/no)\n")
    await writer.drain()

    has_account = (await reader.readline()).decode().strip().lower()

    if has_account == "yes":
        username = await prompt("Enter username:")
        account = load_account(username)
        if not account:
            writer.write(b"No such account.\n")
            return None

        password = await prompt("Enter password:")
        if hash_password(password) != account.password_hash:
            writer.write(b"Incorrect password.\n")
            return None

        writer.write(b"Login successful.\n")
        await writer.drain()
        return account

    else:
        # Create new account
        username = await prompt("Choose a username:")
        if load_account(username):
            writer.write(b"Account already exists.\n")
            return None

        password = await prompt("Choose a password:")
        account = Account(username, hash_password(password))
        save_account(account)

        writer.write(b"Account created.\n")
        await writer.drain()
        return account


# ---------------------------------------------------------
# Character Selection Flow
# ---------------------------------------------------------

async def character_selection_flow(server, reader, writer, account):
    """
    Allows selecting an existing character or creating a new one.
    Integrates with character_creation.py for full character creation.
    """

    from character_creation import create_character
    from accounts import load_character, save_account

    async def prompt(msg):
        writer.write((msg + "\n").encode())
        await writer.drain()
        data = await reader.readline()
        return data.decode().strip()

    # -----------------------------------------------------
    # Existing characters
    # -----------------------------------------------------
    if account.characters:
        writer.write(b"Your characters:\n")
        for c in account.characters:
            writer.write(f" - {c}\n".encode())
        writer.write(b"Type a name to load, or 'new' to create a character.\n")
        await writer.drain()

        choice = (await reader.readline()).decode().strip()

        # Load existing character
        if choice.lower() != "new":
            if choice in account.characters:
                player = load_character(server.world, choice)
                if player:
                    writer.write(b"Character loaded.\n")
                    await writer.drain()
                    return player
                else:
                    writer.write(b"Error loading character.\n")
                    await writer.drain()
                    return None
            else:
                writer.write(b"No such character.\n")
                await writer.drain()
                return None

    # -----------------------------------------------------
    # Create new character
    # -----------------------------------------------------
    writer.write(b"Creating new character...\n")
    await writer.drain()

    player = await create_character(server, reader, writer, account)

    if not player:
        writer.write(b"Character creation failed.\n")
        await writer.drain()
        return None

    writer.write(b"Character ready.\n")
    await writer.drain()

    return player
