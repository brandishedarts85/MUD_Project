"""
Realms of Cyrisea - Account System

Handles:
- Account creation
- Login
- Password hashing
- Account-wide preferences
- Character list
- Character creation entry point
- Character loading and saving
- Persistent account/character paths

Account preferences control the player's overall game
presentation and are intentionally separate from character data.
"""

import json
import hashlib
from pathlib import Path

from core import Player


# ============================================================
# PROJECT PATHS
# ============================================================

# accounts.py lives in:
#
# MUD_Project/
#     account_data/
#     characters/
#     Realms of Cyrisea/
#         accounts.py
#
# Therefore parent.parent is the project root.

PROJECT_ROOT = Path(__file__).resolve().parent.parent

ACCOUNTS_DIR = PROJECT_ROOT / "account_data"
CHARACTERS_DIR = PROJECT_ROOT / "characters"

ACCOUNTS_DIR.mkdir(
    parents=True,
    exist_ok=True
)

CHARACTERS_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# DEFAULT ACCOUNT PREFERENCES
# ============================================================

DEFAULT_PREFERENCES = {
    "units": "imperial",
    "time_format": "12",
    "color": True,
    "room_descriptions": "normal",
    "combat_messages": "normal",
    "prompt_style": "classic",
}


# ============================================================
# PASSWORD HANDLING
# ============================================================

def hash_password(password: str) -> str:
    """
    Hash a password.

    SHA-256 is retained for compatibility with the existing
    account files.
    """

    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


# ============================================================
# ACCOUNT CLASS
# ============================================================

class Account:

    def __init__(
        self,
        username,
        password_hash,
        characters=None,
        preferences=None
    ):
        self.username = username
        self.password_hash = password_hash

        self.characters = (
            characters
            if characters is not None
            else []
        )

        self.preferences = dict(
            DEFAULT_PREFERENCES
        )

        if preferences:
            self.preferences.update(
                preferences
            )

    # --------------------------------------------------------
    # PREFERENCE ACCESS
    # --------------------------------------------------------

    def get_preference(
        self,
        name,
        default=None
    ):
        return self.preferences.get(
            name,
            default
        )

    def set_preference(
        self,
        name,
        value
    ):
        self.preferences[name] = value

    # --------------------------------------------------------
    # SERIALIZATION
    # --------------------------------------------------------

    def to_dict(self):

        return {
            "username": self.username,
            "password_hash": self.password_hash,
            "characters": self.characters,
            "preferences": self.preferences,
        }

    # --------------------------------------------------------
    # DESERIALIZATION
    # --------------------------------------------------------

    @staticmethod
    def from_dict(data):

        return Account(
            username=data["username"],
            password_hash=data["password_hash"],
            characters=data.get(
                "characters",
                []
            ),
            preferences=data.get(
                "preferences",
                {}
            )
        )


# ============================================================
# ACCOUNT FILES
# ============================================================

def account_path(username):
    """
    Return the persistent path for an account.
    """

    safe_username = str(
        username
    ).strip().lower()

    return (
        ACCOUNTS_DIR
        / f"{safe_username}.json"
    )


def load_account(username):
    """
    Load an account from disk.

    Older accounts without preferences are automatically
    upgraded with the current default preference set.

    Returns:
        Account or None
    """

    path = account_path(
        username
    )

    if not path.exists():
        return None

    try:
        with path.open(
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        account = Account.from_dict(
            data
        )

        changed = False

        for (
            preference,
            default_value
        ) in DEFAULT_PREFERENCES.items():

            if (
                preference
                not in account.preferences
            ):

                account.preferences[
                    preference
                ] = default_value

                changed = True

        if changed:
            save_account(
                account
            )

        return account

    except (
        OSError,
        json.JSONDecodeError,
        KeyError,
        TypeError
    ):
        return None


def save_account(account):
    """
    Save an account to disk.
    """

    path = account_path(
        account.username
    )

    with path.open(
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            account.to_dict(),
            f,
            indent=2
        )


# ============================================================
# CHARACTER FILES
# ============================================================

def character_path(name):
    """
    Return the persistent path for a character.
    """

    safe_name = str(
        name
    ).strip().lower()

    return (
        CHARACTERS_DIR
        / f"{safe_name}.json"
    )


def save_character(player):
    """
    Save a Player to disk.

    Persistent references such as inventory and room location
    are stored by VNUM rather than raw Python object references.
    """

    data = {
        "name": player.name,

        "race": getattr(
            player,
            "race",
            None
        ),

        "class": getattr(
            player,
            "class_name",
            None
        ),

        "appearance": getattr(
            player,
            "appearance",
            {}
        ),

        "stats": getattr(
            player,
            "stats",
            {}
        ),

        "inventory": [
            getattr(
                obj,
                "vnum",
                None
            )
            for obj in getattr(
                player,
                "inventory",
                []
            )
            if getattr(
                obj,
                "vnum",
                None
            ) is not None
        ],

        "gold": getattr(
            player,
            "gold",
            0
        ),

        "exp": getattr(
            player,
            "exp",
            0
        ),

        "favor": getattr(
            player,
            "favor",
            0
        ),

        "is_peaceful": getattr(
            player,
            "is_peaceful",
            True
        ),

        "is_deadly": getattr(
            player,
            "is_deadly",
            False
        ),

        "durability_penalty": getattr(
            player,
            "durability_penalty",
            0
        ),

        "fatigue": getattr(
            player,
            "fatigue",
            0
        ),

        "last_death_time": getattr(
            player,
            "last_death_time",
            None
        ),

        "last_corpse": None,

        "location": (
            player.room.vnum
            if getattr(
                player,
                "room",
                None
            )
            else None
        ),

        "human_adaptability": getattr(
            player,
            "human_adaptability",
            False
        ),

        "human_extra_skill_chances": getattr(
            player,
            "human_extra_skill_chances",
            0
        ),
    }

    path = character_path(
        player.name
    )

    with path.open(
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            indent=2
        )


def load_character(
    world,
    name
):
    """
    Load a character from disk.

    Inventory is reconstructed from world object prototypes
    using VNUMs.
    """

    path = character_path(
        name
    )

    if not path.exists():
        return None

    try:
        with path.open(
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

    except (
        OSError,
        json.JSONDecodeError
    ):
        return None

    if "name" not in data:
        return None

    player = Player(
        name=data["name"],
        world=world
    )

    # --------------------------------------------------------
    # Core character data
    # --------------------------------------------------------

    player.stats = data.get(
        "stats",
        {}
    )

    player.race = data.get(
        "race",
        getattr(
            player,
            "race",
            None
        )
    )

    player.class_name = data.get(
        "class",
        getattr(
            player,
            "class_name",
            None
        )
    )

    player.appearance = data.get(
        "appearance",
        {}
    )

    # --------------------------------------------------------
    # Progression / economy
    # --------------------------------------------------------

    player.gold = data.get(
        "gold",
        0
    )

    player.exp = data.get(
        "exp",
        0
    )

    player.favor = data.get(
        "favor",
        0
    )

    # --------------------------------------------------------
    # PvP state
    # --------------------------------------------------------

    player.is_peaceful = data.get(
        "is_peaceful",
        True
    )

    player.is_deadly = data.get(
        "is_deadly",
        False
    )

    # --------------------------------------------------------
    # Condition / death state
    # --------------------------------------------------------

    player.durability_penalty = data.get(
        "durability_penalty",
        0
    )

    player.fatigue = data.get(
        "fatigue",
        0
    )

    player.last_death_time = data.get(
        "last_death_time",
        None
    )

    # --------------------------------------------------------
    # Human adaptability
    # --------------------------------------------------------

    player.human_adaptability = data.get(
        "human_adaptability",
        False
    )

    player.human_extra_skill_chances = data.get(
        "human_extra_skill_chances",
        0
    )

    # --------------------------------------------------------
    # Inventory
    # --------------------------------------------------------

    inv_vnums = data.get(
        "inventory",
        []
    )

    for vnum in inv_vnums:

        if vnum in world.objects:

            prototype = world.objects[vnum]

            try:
                item = prototype.clone()
            except AttributeError:
                continue

            player.inventory.append(
                item
            )

    # --------------------------------------------------------
    # Location
    # --------------------------------------------------------

    location = data.get(
        "location",
        None
    )

    if location is not None:

        try:
            room = world.rooms.get(
                location
            )
        except AttributeError:
            room = None

        if room is not None:

            player.room = room

            if hasattr(
                room,
                "players"
            ):

                if player not in room.players:

                    room.players.append(
                        player
                    )

    return player


# ============================================================
# ACCOUNT PREFERENCE SETUP
# ============================================================

async def choose_account_preferences(
    writer,
    reader
):
    """
    Configure the global preferences for a new account.

    These preferences belong to the account rather than to
    individual characters.
    """

    async def send(message=""):

        writer.write(
            (
                message + "\n"
            ).encode("utf-8")
        )

        await writer.drain()

    async def prompt(message):

        await send(message)

        data = await reader.readline()

        if not data:
            return None

        return data.decode(
            "utf-8",
            errors="replace"
        ).strip()

    async def choose(
        title,
        options
    ):
        """
        Display a list of choices and return the selected key.

        Unambiguous prefixes are accepted.
        """

        await send()
        await send(title)

        for key, description in options:

            await send(
                f" - {key}: {description}"
            )

        while True:

            value = await prompt(
                "> "
            )

            if value is None:
                return None

            value = value.lower()

            for key, description in options:

                if value == key.lower():

                    return key

            matches = [
                key
                for key, description in options
                if key.lower().startswith(
                    value
                )
            ]

            if len(matches) == 1:

                return matches[0]

            await send(
                "Invalid choice. "
                "Enter one of the listed options."
            )

    # --------------------------------------------------------
    # MEASUREMENT SYSTEM
    # --------------------------------------------------------

    units = await choose(
        "Measurement system:",
        [
            (
                "imperial",
                "Feet/inches and pounds."
            ),
            (
                "metric",
                "Centimeters/meters and kilograms."
            ),
        ]
    )

    if units is None:
        return None

    # --------------------------------------------------------
    # TIME FORMAT
    # --------------------------------------------------------

    time_format = await choose(
        "Time display:",
        [
            (
                "12",
                "12-hour clock."
            ),
            (
                "24",
                "24-hour clock."
            ),
        ]
    )

    if time_format is None:
        return None

    # --------------------------------------------------------
    # ANSI COLOR
    # --------------------------------------------------------

    color_choice = await choose(
        "Color display:",
        [
            (
                "ansi",
                "Use ANSI terminal colors."
            ),
            (
                "mono",
                "Use monochrome text."
            ),
        ]
    )

    if color_choice is None:
        return None

    # --------------------------------------------------------
    # ROOM DESCRIPTIONS
    # --------------------------------------------------------

    room_descriptions = await choose(
        "Room descriptions:",
        [
            (
                "normal",
                "Show full room descriptions."
            ),
            (
                "brief",
                "Use shorter descriptions after the first visit."
            ),
        ]
    )

    if room_descriptions is None:
        return None

    # --------------------------------------------------------
    # COMBAT MESSAGES
    # --------------------------------------------------------

    combat_messages = await choose(
        "Combat messages:",
        [
            (
                "normal",
                "Standard combat messages."
            ),
            (
                "verbose",
                "Show additional combat details."
            ),
        ]
    )

    if combat_messages is None:
        return None

    # --------------------------------------------------------
    # PROMPT STYLE
    # --------------------------------------------------------

    prompt_style = await choose(
        "Prompt style:",
        [
            (
                "classic",
                "Traditional MUD-style prompt."
            ),
            (
                "compact",
                "Shorter prompt using less screen space."
            ),
        ]
    )

    if prompt_style is None:
        return None

    # --------------------------------------------------------
    # RETURN PREFERENCES
    # --------------------------------------------------------

    return {
        "units": units,
        "time_format": time_format,
        "color": (
            color_choice == "ansi"
        ),
        "room_descriptions": room_descriptions,
        "combat_messages": combat_messages,
        "prompt_style": prompt_style,
    }


# ============================================================
# LOGIN FLOW
# ============================================================

async def login_flow(
    server,
    reader,
    writer
):
    """
    Handle account login and account creation.

    Invalid credentials do NOT disconnect the player.

    The player is returned to the username/password prompts
    until they successfully authenticate or disconnect.
    """

    async def prompt(message):

        writer.write(
            (
                message + "\n"
            ).encode("utf-8")
        )

        await writer.drain()

        data = await reader.readline()

        if not data:
            return None

        return data.decode(
            "utf-8",
            errors="replace"
        ).strip()

    # ========================================================
    # WELCOME
    # ========================================================

    writer.write(
        b"\n"
        b"Welcome to Realms of Cyrisea!\n"
        b"\n"
        b"[Press Enter to Continue...]\n"
    )

    await writer.drain()

    data = await reader.readline()

    if not data:
        return None

    # ========================================================
    # EXISTING ACCOUNT OR NEW ACCOUNT?
    # ========================================================

    while True:

        response = await prompt(
            "Do you have an account? (yes/no)"
        )

        if response is None:
            return None

        answer = response.lower()

        if answer in (
            "yes",
            "y"
        ):
            break

        if answer in (
            "no",
            "n"
        ):
            break

        writer.write(
            b"Please answer yes or no.\n"
        )

        await writer.drain()

    # ========================================================
    # EXISTING ACCOUNT
    # ========================================================

    if answer in (
        "yes",
        "y"
    ):

        while True:

            username = await prompt(
                "Enter username:"
            )

            if username is None:
                return None

            username = username.strip()

            if not username:

                writer.write(
                    b"Username cannot be empty. "
                    b"Please try again.\n"
                )

                await writer.drain()

                continue

            account = load_account(
                username
            )

            password = await prompt(
                "Enter password:"
            )

            if password is None:
                return None

            if (
                account is None
                or hash_password(password)
                != account.password_hash
            ):

                writer.write(
                    b"Invalid username or password. "
                    b"Please try again.\n"
                )

                await writer.drain()

                continue

            writer.write(
                b"Login successful.\n"
            )

            await writer.drain()

            return account

    # ========================================================
    # NEW ACCOUNT
    # ========================================================

    while True:

        username = await prompt(
            "Choose a username:"
        )

        if username is None:
            return None

        username = username.strip()

        if not username:

            writer.write(
                b"Username cannot be empty. "
                b"Please try again.\n"
            )

            await writer.drain()

            continue

        # ----------------------------------------------------
        # Username validation
        # ----------------------------------------------------

        if len(username) < 3 or len(username) > 20:

            writer.write(
                b"Username must be between "
                b"3 and 20 characters. "
                b"Please try again.\n"
            )

            await writer.drain()

            continue

        if not username.replace(
            "_",
            ""
        ).isalnum():

            writer.write(
                b"Username may contain letters, "
                b"numbers, and underscores only. "
                b"Please try again.\n"
            )

            await writer.drain()

            continue

        # ----------------------------------------------------
        # Existing account check
        # ----------------------------------------------------

        if load_account(username) is not None:

            writer.write(
                b"Account already exists. "
                b"Please choose another username.\n"
            )

            await writer.drain()

            continue

        break

    # --------------------------------------------------------
    # Password
    # --------------------------------------------------------

    while True:

        password = await prompt(
            "Choose a password:"
        )

        if password is None:
            return None

        if len(password) < 4:

            writer.write(
                b"Password must be at least "
                b"4 characters long. "
                b"Please try again.\n"
            )

            await writer.drain()

            continue

        break

    # --------------------------------------------------------
    # Account creation
    # --------------------------------------------------------

    writer.write(
        b"\n"
        b"Account created.\n"
        b"\n"
        b"Now let's configure your "
        b"account preferences.\n"
    )

    await writer.drain()

    preferences = await choose_account_preferences(
        writer,
        reader
    )

    if preferences is None:
        return None

    # --------------------------------------------------------
    # Create account with preferences
    # --------------------------------------------------------

    account = Account(
        username=username,
        password_hash=hash_password(
            password
        ),
        preferences=preferences
    )

    save_account(
        account
    )

    writer.write(
        b"\n"
        b"Account preferences saved.\n"
    )

    await writer.drain()

    return account


# ============================================================
# CHARACTER SELECTION
# ============================================================

async def character_selection_flow(
    server,
    reader,
    writer,
    account
):
    """
    Load an existing character or enter character creation.
    """

    from character_creation import create_character

    async def prompt(message):

        writer.write(
            (
                message + "\n"
            ).encode("utf-8")
        )

        await writer.drain()

        data = await reader.readline()

        if not data:
            return None

        return data.decode(
            "utf-8",
            errors="replace"
        ).strip()

    # ========================================================
    # EXISTING CHARACTERS
    # ========================================================

    if account.characters:

        while True:

            writer.write(
                b"Your characters:\n"
            )

            for character_name in account.characters:

                writer.write(
                    (
                        f" - {character_name}\n"
                    ).encode("utf-8")
                )

            writer.write(
                b"Type a character name to load, "
                b"or 'new' to create a character.\n"
            )

            await writer.drain()

            choice = await prompt(
                "Character:"
            )

            if choice is None:
                return None

            choice = choice.strip()

            # ------------------------------------------------
            # New character
            # ------------------------------------------------

            if choice.lower() == "new":
                break

            # ------------------------------------------------
            # Load character
            # ------------------------------------------------

            matched_name = None

            for character_name in account.characters:

                if (
                    character_name.lower()
                    == choice.lower()
                ):

                    matched_name = character_name
                    break

            if matched_name is None:

                writer.write(
                    b"No such character. "
                    b"Please try again.\n"
                )

                await writer.drain()

                continue

            player = load_character(
                server.world,
                matched_name
            )

            if player is None:

                writer.write(
                    b"Error loading character.\n"
                )

                await writer.drain()

                continue

            writer.write(
                b"Character loaded.\n"
            )

            await writer.drain()

            return player

    # ========================================================
    # CHARACTER CREATION
    # ========================================================

    writer.write(
        b"Creating new character...\n"
    )

    await writer.drain()

    player = await create_character(
        server,
        reader,
        writer,
        account
    )

    if player is None:

        writer.write(
            b"Character creation failed.\n"
        )

        await writer.drain()

        return None

    writer.write(
        b"Character ready.\n"
    )

    await writer.drain()

    return player