"""
Realms of Cyrisea - Character Creation System

Character creation flow:

    Name
      -> Race
      -> Class
      -> Appearance
      -> Build
      -> Stats
      -> PvP
      -> Preview
      -> Confirmation
      -> Player creation
      -> Starting equipment
      -> Starting room
      -> Save

Account-wide preferences determine how physical measurements
are entered and displayed.

Internally, character height and weight are always stored as:

    height_cm
    weight_kg

This keeps character data independent of the player's
account presentation preferences.
"""

import random
import re

from core import Player


# =========================================================
# STAT DEFINITIONS
# =========================================================

STAT_NAMES = (
    "MIG",
    "FIN",
    "VIT",
    "ARC",
    "SPI",
    "PRE",
)

STAT_LABELS = {
    "MIG": "Might",
    "FIN": "Finesse",
    "VIT": "Vitality",
    "ARC": "Arcana",
    "SPI": "Spirit",
    "PRE": "Presence",
}


# =========================================================
# NAME VALIDATION
# =========================================================

BLACKLIST = {
    "admin",
    "builder",
    "moderator",
    "fuck",
    "shit",
    "bitch",
    "cunt",
    "hitler",
    "nazi",
    "slave",
    "rapist",
}


def validate_name(name):
    name = name.strip()

    if len(name) < 3 or len(name) > 16:
        return False, "Name must be between 3 and 16 characters."

    if not name.isalpha():
        return False, "Name must contain only letters."

    if name.lower() in BLACKLIST:
        return False, "That name is not allowed."

    return True, ""


# =========================================================
# CHOICE RESOLUTION
# =========================================================

def resolve_choice(value, options):
    value = value.strip().lower()
    options = [
        str(option).lower()
        for option in options
    ]

    if not value:
        return None

    if value in options:
        return value

    matches = [
        option
        for option in options
        if option.startswith(value)
    ]

    if len(matches) == 1:
        return matches[0]

    return None


# =========================================================
# RACES
# =========================================================

RACES = {
    "human": {
        "description": "Adaptable and versatile, with no major weakness.",
        "mod": {},
        "choice": True,
        "start_zone": "sunspire",
    },

    "elf": {
        "description": (
            "Agile and attuned to arcane forces, "
            "but physically frail."
        ),
        "mod": {
            "FIN": 1,
            "ARC": 1,
            "VIT": -1,
        },
        "choice": False,
        "start_zone": "crystalwood",
    },

    "dwarf": {
        "description": "Strong and durable, but less graceful.",
        "mod": {
            "MIG": 1,
            "VIT": 1,
            "FIN": -1,
        },
        "choice": False,
        "start_zone": "obsidian_order",
    },

    "frostborn": {
        "description": (
            "Hardy and spiritually resilient, "
            "but less socially imposing."
        ),
        "mod": {
            "VIT": 1,
            "SPI": 1,
            "PRE": -1,
        },
        "choice": False,
        "start_zone": "frostpeak",
    },
}


# =========================================================
# CLASSES
# =========================================================

CLASSES = {
    "warrior": {
        "description": "A durable frontline fighter.",
        "mod": {
            "MIG": 1,
            "VIT": 1,
            "ARC": -1,
        },
        "start_items": [1001, 1002],
    },

    "ranger": {
        "description": (
            "A mobile fighter skilled in ranged combat "
            "and survival."
        ),
        "mod": {
            "FIN": 1,
            "PRE": 1,
            "VIT": -1,
        },
        "start_items": [1003],
    },

    "mage": {
        "description": "A practitioner of arcane magic.",
        "mod": {
            "ARC": 1,
            "SPI": 1,
            "MIG": -1,
        },
        "start_items": [1004],
    },

    "cleric": {
        "description": "A spiritual champion and protector.",
        "mod": {
            "SPI": 1,
            "PRE": 1,
            "FIN": -1,
        },
        "start_items": [1005],
    },
}


# =========================================================
# APPEARANCE
# =========================================================

SKIN_TONES = [
    "pale",
    "fair",
    "tan",
    "olive",
    "brown",
    "dark",
]

HAIR_COLORS = [
    "black",
    "brown",
    "blonde",
    "red",
    "white",
    "silver",
]

EYE_COLORS = [
    "brown",
    "blue",
    "green",
    "hazel",
    "gray",
    "amber",
]


APPEARANCE_MODIFIERS = {
    "skin": {
        "pale": {
            "ARC": 1,
            "VIT": -1,
        },
        "fair": {
            "PRE": 1,
            "MIG": -1,
        },
        "tan": {
            "VIT": 1,
            "ARC": -1,
        },
        "olive": {
            "FIN": 1,
            "PRE": -1,
        },
        "brown": {
            "MIG": 1,
            "ARC": -1,
        },
        "dark": {
            "SPI": 1,
            "PRE": -1,
        },
    },

    "hair": {
        "black": {
            "MIG": 1,
            "PRE": -1,
        },
        "brown": {
            "PRE": 1,
            "ARC": -1,
        },
        "blonde": {
            "PRE": 1,
            "VIT": -1,
        },
        "red": {
            "MIG": 1,
            "SPI": -1,
        },
        "white": {
            "SPI": 1,
            "FIN": -1,
        },
        "silver": {
            "ARC": 1,
            "MIG": -1,
        },
    },

    "eyes": {
        "brown": {
            "VIT": 1,
            "ARC": -1,
        },
        "blue": {
            "ARC": 1,
            "MIG": -1,
        },
        "green": {
            "FIN": 1,
            "VIT": -1,
        },
        "hazel": {
            "PRE": 1,
            "SPI": -1,
        },
        "gray": {
            "SPI": 1,
            "PRE": -1,
        },
        "amber": {
            "ARC": 1,
            "FIN": -1,
        },
    },
}


# =========================================================
# BUILDS
# =========================================================

BUILDS = {
    "frail": {
        "description": (
            "Light-framed and naturally suited "
            "to magical ability."
        ),
        "mod": {
            "ARC": 1,
            "MIG": -1,
        },
    },

    "average": {
        "description": "A balanced physical build.",
        "mod": {},
    },

    "muscular": {
        "description": (
            "Powerfully built, but somewhat less agile."
        ),
        "mod": {
            "MIG": 1,
            "FIN": -1,
        },
    },

    "heavy": {
        "description": (
            "Broad and durable, but less agile."
        ),
        "mod": {
            "VIT": 1,
            "FIN": -1,
        },
    },
}


# =========================================================
# STAT GENERATION
# =========================================================

def roll_2d6():
    return (
        random.randint(1, 6)
        + random.randint(1, 6)
    )


def generate_rolled_stats():
    return {
        stat: roll_2d6()
        for stat in STAT_NAMES
    }


def generate_pointbuy_stats():
    return {
        stat: 8
        for stat in STAT_NAMES
    }


def apply_modifier_dict(stats, modifiers):
    for stat, amount in modifiers.items():

        if stat in stats:
            stats[stat] += amount


def calculate_appearance_modifiers(
    skin,
    hair,
    eyes,
):
    modifiers = {}

    selections = (
        ("skin", skin),
        ("hair", hair),
        ("eyes", eyes),
    )

    for category, choice in selections:

        category_modifiers = (
            APPEARANCE_MODIFIERS
            .get(category, {})
            .get(choice, {})
        )

        for stat, amount in category_modifiers.items():

            modifiers[stat] = (
                modifiers.get(stat, 0)
                + amount
            )

    return modifiers


def clamp_creation_stats(stats):
    for stat in STAT_NAMES:

        stats[stat] = max(
            3,
            min(
                17,
                stats[stat],
            ),
        )


# =========================================================
# MEASUREMENT HELPERS
# =========================================================

def get_account_units(account):
    """
    Return the account's preferred measurement system.

    Internally the game uses:
        imperial
        metric

    If an older account has no preference, Imperial is used.
    """

    preferences = getattr(
        account,
        "preferences",
        {},
    )

    units = preferences.get(
        "units",
        "imperial",
    )

    if units not in (
        "imperial",
        "metric",
    ):
        units = "imperial"

    return units


def imperial_height_to_cm(feet, inches):
    """
    Convert feet/inches to centimeters.
    """

    total_inches = (
        feet * 12
        + inches
    )

    return round(
        total_inches * 2.54,
        1,
    )


def imperial_weight_to_kg(pounds):
    """
    Convert pounds to kilograms.
    """

    return round(
        pounds * 0.45359237,
        1,
    )


def cm_to_imperial_height(height_cm):
    """
    Convert centimeters to feet and inches.

    Returns:
        (feet, inches)
    """

    total_inches = (
        height_cm / 2.54
    )

    feet = int(
        total_inches // 12
    )

    inches = round(
        total_inches - (feet * 12)
    )

    # Handle rounding 11.99 -> 12.
    if inches == 12:

        feet += 1
        inches = 0

    return feet, inches


def kg_to_pounds(weight_kg):
    """
    Convert kilograms to pounds.
    """

    return round(
        weight_kg * 2.20462262,
        1,
    )


def parse_imperial_height(value):
    """
    Parse common Imperial height formats.

    Accepted examples:

        5'8"
        5'8
        5 8
        5ft 8in
        5 feet 8 inches
        5

    A bare number is interpreted as feet.
    """

    value = (
        value
        .strip()
        .lower()
    )

    value = value.replace(
        "feet",
        "ft",
    )

    value = value.replace(
        "foot",
        "ft",
    )

    value = value.replace(
        "inches",
        "in",
    )

    value = value.replace(
        "inch",
        "in",
    )

    # Standard 5'8" format.
    match = re.fullmatch(
        r"\s*(\d+)\s*[' ]\s*(\d+(?:\.\d+)?)\s*\"?\s*",
        value,
    )

    if match:

        feet = int(
            match.group(1)
        )

        inches = float(
            match.group(2)
        )

        return feet, inches

    # 5ft 8in format.
    match = re.fullmatch(
        r"\s*(\d+)\s*ft\s*(\d+(?:\.\d+)?)?\s*in?\s*",
        value,
    )

    if match:

        feet = int(
            match.group(1)
        )

        inches = float(
            match.group(2)
            or 0
        )

        return feet, inches

    # Two numbers separated by whitespace.
    match = re.fullmatch(
        r"\s*(\d+)\s+(\d+(?:\.\d+)?)\s*",
        value,
    )

    if match:

        feet = int(
            match.group(1)
        )

        inches = float(
            match.group(2)
        )

        return feet, inches

    # Bare feet.
    match = re.fullmatch(
        r"\s*(\d+(?:\.\d+)?)\s*(?:ft)?\s*",
        value,
    )

    if match:

        feet_value = float(
            match.group(1)
        )

        feet = int(
            feet_value
        )

        inches = (
            feet_value - feet
        ) * 12

        return feet, inches

    return None


# =========================================================
# FORMATTING
# =========================================================

def format_modifier(amount):

    if amount > 0:
        return f"+{amount}"

    return str(amount)


def format_stat_breakdown(
    stat,
    natural,
    race_mod,
    class_mod,
    build_mod,
    appearance_mod,
    final_value,
):
    pieces = [
        str(natural)
    ]

    if race_mod:

        pieces.append(
            format_modifier(
                race_mod
            )
        )

    if class_mod:

        pieces.append(
            format_modifier(
                class_mod
            )
        )

    if build_mod:

        pieces.append(
            format_modifier(
                build_mod
            )
        )

    if appearance_mod:

        pieces.append(
            format_modifier(
                appearance_mod
            )
        )

    calculation = " ".join(
        pieces
    )

    return (
        f"{stat:>3} "
        f"{STAT_LABELS[stat]:<10} "
        f"{calculation:<18} "
        f"= {final_value}"
    )


# =========================================================
# MAIN CHARACTER CREATION
# =========================================================

async def create_character(
    server,
    reader,
    writer,
    account,
):

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

            raise ConnectionError(
                "Client disconnected during "
                "character creation."
            )

        decoded = data.decode(
            "utf-8",
            errors="replace",
        )

        return decoded.strip()

    async def choose(
        title,
        options,
        description_map=None,
        allow_back=False,
    ):

        options = list(options)

        await send()
        await send(title)

        for option in options:

            if (
                description_map
                and option in description_map
            ):

                await send(
                    f" - {option}: "
                    f"{description_map[option]}"
                )

            else:

                await send(
                    f" - {option}"
                )

        if allow_back:

            await send(
                " - back"
            )

        while True:

            value = (
                await prompt("> ")
            ).lower()

            if (
                allow_back
                and value == "back"
            ):

                return "back"

            result = resolve_choice(
                value,
                options,
            )

            if result is not None:

                return result

            await send(
                "Invalid choice. Enter one "
                "of the listed options."
            )

    # =====================================================
    # CREATION LOOP
    # =====================================================

    while True:

        # -------------------------------------------------
        # NAME
        # -------------------------------------------------

        while True:

            name = await prompt(
                "Enter character name:"
            )

            valid, message = (
                validate_name(name)
            )

            if valid:
                break

            await send(
                message
            )

        # -------------------------------------------------
        # RACE
        # -------------------------------------------------

        race = await choose(
            "Choose a race:",
            RACES.keys(),
            {
                race_name:
                    RACES[race_name][
                        "description"
                    ]
                for race_name in RACES
            },
        )

        # -------------------------------------------------
        # CLASS
        # -------------------------------------------------

        class_name = await choose(
            "Choose a class:",
            CLASSES.keys(),
            {
                class_name:
                    CLASSES[class_name][
                        "description"
                    ]
                for class_name in CLASSES
            },
        )

        # -------------------------------------------------
        # ACCOUNT UNITS
        # -------------------------------------------------

        units = get_account_units(
            account
        )

        # -------------------------------------------------
        # APPEARANCE
        # -------------------------------------------------

        await send()

        randomize = (
            await prompt(
                "Randomize appearance? (yes/no)"
            )
        ).lower()

        while randomize not in (
            "yes",
            "no",
            "y",
            "n",
        ):

            await send(
                "Please enter yes or no."
            )

            randomize = (
                await prompt("> ")
            ).lower()

        if randomize in (
            "yes",
            "y",
        ):

            skin = random.choice(
                SKIN_TONES
            )

            hair = random.choice(
                HAIR_COLORS
            )

            eyes = random.choice(
                EYE_COLORS
            )

            # Randomize canonical metric values.
            height_cm = random.randint(
                150,
                210,
            )

            weight_kg = random.randint(
                50,
                140,
            )

            await send()
            await send(
                "Appearance randomized:"
            )

            await send(
                f" - Skin: {skin}"
            )

            await send(
                f" - Hair: {hair}"
            )

            await send(
                f" - Eyes: {eyes}"
            )

            if units == "metric":

                await send(
                    f" - Height: "
                    f"{height_cm} cm"
                )

                await send(
                    f" - Weight: "
                    f"{weight_kg} kg"
                )

            else:

                feet, inches = (
                    cm_to_imperial_height(
                        height_cm
                    )
                )

                pounds = kg_to_pounds(
                    weight_kg
                )

                await send(
                    f" - Height: "
                    f"{feet}'{inches}\""
                )

                await send(
                    f" - Weight: "
                    f"{pounds} lbs"
                )

        else:

            # -------------------------------------------------
            # SKIN
            # -------------------------------------------------

            skin = await choose(
                "Choose skin tone:",
                SKIN_TONES,
            )

            # -------------------------------------------------
            # HAIR
            # -------------------------------------------------

            hair = await choose(
                "Choose hair color:",
                HAIR_COLORS,
            )

            # -------------------------------------------------
            # EYES
            # -------------------------------------------------

            eyes = await choose(
                "Choose eye color:",
                EYE_COLORS,
            )

            # -------------------------------------------------
            # HEIGHT
            # -------------------------------------------------

            while True:

                if units == "metric":

                    height_text = await prompt(
                        "Enter height in cm "
                        "(100-250):"
                    )

                    try:

                        height_cm = float(
                            height_text
                        )

                    except ValueError:

                        await send(
                            "Height must be a number."
                        )

                        continue

                    if (
                        100
                        <= height_cm
                        <= 250
                    ):

                        height_cm = round(
                            height_cm,
                            1,
                        )

                        break

                    await send(
                        "Height must be between "
                        "100 and 250 cm."
                    )

                else:

                    height_text = await prompt(
                        "Enter height "
                        "(feet/inches, e.g. 5'8\"):"
                    )

                    parsed = (
                        parse_imperial_height(
                            height_text
                        )
                    )

                    if parsed is None:

                        await send(
                            "Please enter a valid "
                            "height such as 5'8\"."
                        )

                        continue

                    feet, inches = parsed

                    if (
                        feet < 3
                        or feet > 8
                        or inches < 0
                        or inches >= 12
                    ):

                        await send(
                            "Height must be between "
                            "3'0\" and 8'0\"."
                        )

                        continue

                    height_cm = (
                        imperial_height_to_cm(
                            feet,
                            inches,
                        )
                    )

                    if (
                        height_cm < 100
                        or height_cm > 250
                    ):

                        await send(
                            "That height is outside "
                            "the allowed range."
                        )

                        continue

                    break

            # -------------------------------------------------
            # WEIGHT
            # -------------------------------------------------

            while True:

                if units == "metric":

                    weight_text = await prompt(
                        "Enter weight in kg "
                        "(25-300):"
                    )

                    try:

                        weight_kg = float(
                            weight_text
                        )

                    except ValueError:

                        await send(
                            "Weight must be a number."
                        )

                        continue

                    if (
                        25
                        <= weight_kg
                        <= 300
                    ):

                        weight_kg = round(
                            weight_kg,
                            1,
                        )

                        break

                    await send(
                        "Weight must be between "
                        "25 and 300 kg."
                    )

                else:

                    weight_text = await prompt(
                        "Enter weight in pounds "
                        "(55-661):"
                    )

                    try:

                        pounds = float(
                            weight_text
                        )

                    except ValueError:

                        await send(
                            "Weight must be a number."
                        )

                        continue

                    if (
                        55
                        <= pounds
                        <= 661
                    ):

                        weight_kg = (
                            imperial_weight_to_kg(
                                pounds
                            )
                        )

                        break

                    await send(
                        "Weight must be between "
                        "55 and 661 pounds."
                    )

        # -------------------------------------------------
        # BUILD
        # -------------------------------------------------

        await send()
        await send(
            "Recommended builds:"
        )

        if class_name == "warrior":

            await send(
                " - muscular: favors Might"
            )

            await send(
                " - heavy: favors Vitality"
            )

        elif class_name == "ranger":

            await send(
                " - muscular: stronger physical attacks"
            )

            await send(
                " - average: balanced"
            )

            await send(
                " - frail: favors Arcana"
            )

        elif class_name == "mage":

            await send(
                " - frail: favors Arcana"
            )

            await send(
                " - average: balanced"
            )

        elif class_name == "cleric":

            await send(
                " - heavy: favors Vitality"
            )

            await send(
                " - average: balanced"
            )

        build = await choose(
            "Choose body build:",
            BUILDS.keys(),
            {
                build_name:
                    BUILDS[build_name][
                        "description"
                    ]
                for build_name in BUILDS
            },
        )

        # -------------------------------------------------
        # STAT METHOD
        # -------------------------------------------------

        await send()
        await send(
            "Choose stat generation method:"
        )

        await send(
            " - roll: six stats generated with 2d6"
        )

        await send(
            " - pointbuy: traditional 27-point system"
        )

        while True:

            method = (
                await prompt("> ")
            ).lower()

            resolved_method = resolve_choice(
                method,
                [
                    "roll",
                    "pointbuy",
                ],
            )

            if resolved_method:

                method = resolved_method
                break

            await send(
                "Invalid method. "
                "Enter roll or pointbuy."
            )

        # -------------------------------------------------
        # NATURAL STATS
        # -------------------------------------------------

        if method == "roll":

            natural_stats = (
                generate_rolled_stats()
            )

            await send()
            await send(
                "Your natural 2d6 rolls are:"
            )

            for stat in STAT_NAMES:

                await send(
                    f" - {stat} "
                    f"({STAT_LABELS[stat]}): "
                    f"{natural_stats[stat]}"
                )

        else:

            natural_stats = (
                generate_pointbuy_stats()
            )

            remaining_points = 27

            await send()
            await send(
                "Point-buy begins with all stats at 8."
            )

            await send(
                "You have 27 points to distribute."
            )

            await send(
                "Each stat may be raised to a maximum of 15."
            )

            for stat in STAT_NAMES:

                while True:

                    value_text = await prompt(
                        f"{stat} "
                        f"({STAT_LABELS[stat]}) "
                        f"current={natural_stats[stat]} "
                        f"points={remaining_points}:"
                    )

                    try:

                        value = int(
                            value_text
                        )

                    except ValueError:

                        await send(
                            "Enter a whole number."
                        )

                        continue

                    if (
                        value < 8
                        or value > 15
                    ):

                        await send(
                            "Stats must remain "
                            "between 8 and 15 "
                            "during point-buy."
                        )

                        continue

                    cost = (
                        value
                        - natural_stats[stat]
                    )

                    if cost > remaining_points:

                        await send(
                            "You do not have enough points."
                        )

                        continue

                    natural_stats[stat] = value

                    remaining_points -= cost

                    break

            await send(
                f"Points remaining: "
                f"{remaining_points}"
            )

        # -------------------------------------------------
        # MODIFIERS
        # -------------------------------------------------

        race_modifiers = dict(
            RACES[race].get(
                "mod",
                {},
            )
        )

        class_modifiers = dict(
            CLASSES[class_name].get(
                "mod",
                {},
            )
        )

        build_modifiers = dict(
            BUILDS[build].get(
                "mod",
                {},
            )
        )

        appearance_modifiers = (
            calculate_appearance_modifiers(
                skin,
                hair,
                eyes,
            )
        )

        # -------------------------------------------------
        # HUMAN ADAPTABILITY
        # -------------------------------------------------

        human_choice = None

        if RACES[race].get(
            "choice"
        ):

            await send()
            await send(
                "Human adaptability: "
                "choose one stat for +1."
            )

            human_choice = await choose(
                "Choose a stat:",
                STAT_NAMES,
                {
                    stat:
                        STAT_LABELS[stat]
                    for stat in STAT_NAMES
                },
            )

            race_modifiers[
                human_choice
            ] = (
                race_modifiers.get(
                    human_choice,
                    0,
                )
                + 1
            )

        # -------------------------------------------------
        # FINAL STATS
        # -------------------------------------------------

        final_stats = {}

        for stat in STAT_NAMES:

            value = (
                natural_stats[stat]
            )

            value += race_modifiers.get(
                stat,
                0,
            )

            value += class_modifiers.get(
                stat,
                0,
            )

            value += build_modifiers.get(
                stat,
                0,
            )

            value += appearance_modifiers.get(
                stat,
                0,
            )

            final_stats[stat] = value

        clamp_creation_stats(
            final_stats
        )

        # -------------------------------------------------
        # PVP
        # -------------------------------------------------

        mode = await choose(
            "Choose PvP mode:",
            [
                "peaceful",
                "deadly",
            ],
            {
                "peaceful":
                    "You cannot participate in open PvP.",

                "deadly":
                    "You may participate in open PvP.",
            },
        )

        # -------------------------------------------------
        # PREVIEW
        # -------------------------------------------------

        await send()
        await send(
            "=" * 56
        )

        await send(
            "              CHARACTER PREVIEW"
        )

        await send(
            "=" * 56
        )

        await send(
            f"Name:       {name}"
        )

        await send(
            f"Race:       {race}"
        )

        await send(
            f"Class:      {class_name}"
        )

        await send(
            "PvP Mode:   "
            + (
                "Peaceful"
                if mode == "peaceful"
                else "Deadly"
            )
        )

        await send()

        await send(
            "Appearance:"
        )

        await send(
            f"  Skin:     {skin}"
        )

        await send(
            f"  Hair:     {hair}"
        )

        await send(
            f"  Eyes:     {eyes}"
        )

        if units == "metric":

            await send(
                f"  Height:   "
                f"{height_cm} cm"
            )

            await send(
                f"  Weight:   "
                f"{weight_kg} kg"
            )

        else:

            feet, inches = (
                cm_to_imperial_height(
                    height_cm
                )
            )

            pounds = kg_to_pounds(
                weight_kg
            )

            await send(
                f"  Height:   "
                f"{feet}'{inches}\""
            )

            await send(
                f"  Weight:   "
                f"{pounds} lbs"
            )

        await send(
            f"  Build:    {build}"
        )

        await send()
        await send(
            "Stats:"
        )

        await send(
            "      Stat       Calculation           Final"
        )

        await send(
            "      ---------------------------------------"
        )

        for stat in STAT_NAMES:

            await send(
                format_stat_breakdown(
                    stat,
                    natural_stats[stat],
                    race_modifiers.get(
                        stat,
                        0,
                    ),
                    class_modifiers.get(
                        stat,
                        0,
                    ),
                    build_modifiers.get(
                        stat,
                        0,
                    ),
                    appearance_modifiers.get(
                        stat,
                        0,
                    ),
                    final_stats[stat],
                )
            )

        await send()

        await send(
            "Starting Region: "
            f"{RACES[race]['start_zone']}"
        )

        if human_choice:

            await send(
                "Human adaptability: "
                f"+1 {human_choice}"
            )

        await send(
            "=" * 56
        )

        # -------------------------------------------------
        # CONFIRMATION
        # -------------------------------------------------

        await send()

        await send(
            "Confirm character? "
            "(yes / no / change)"
        )

        while True:

            confirm = (
                await prompt("> ")
            ).lower()

            if confirm in (
                "yes",
                "y",
            ):

                break

            if confirm in (
                "no",
                "n",
            ):

                await send(
                    "Character creation cancelled."
                )

                return None

            if confirm in (
                "change",
                "c",
            ):

                await send(
                    "Returning to character creation..."
                )

                break

            await send(
                "Please enter yes, no, or change."
            )

        if confirm in (
            "change",
            "c",
        ):

            continue

        # =================================================
        # CREATE PLAYER
        # =================================================

        player = Player(
            name=name,
            world=server.world,
        )

        player.race = race

        player.class_name = (
            class_name
        )

        player.stats.update(
            final_stats
        )

        # -------------------------------------------------
        # APPEARANCE
        # -------------------------------------------------

        player.appearance = {
            "skin": skin,
            "hair": hair,
            "eyes": eyes,

            # Canonical internal measurements.
            "height_cm": height_cm,
            "weight_kg": weight_kg,

            "build": build,
        }

        # -------------------------------------------------
        # PVP
        # -------------------------------------------------

        player.is_peaceful = (
            mode == "peaceful"
        )

        player.is_deadly = (
            mode == "deadly"
        )

        # -------------------------------------------------
        # HUMAN ADAPTABILITY
        # -------------------------------------------------

        player.human_adaptability = (
            race == "human"
        )

        player.human_extra_skill_chances = 0

        # -------------------------------------------------
        # STARTING ROOM
        # -------------------------------------------------

        start_zone = RACES[race][
            "start_zone"
        ]

        starting_room = None

        for room in (
            server.world.rooms.values()
        ):

            region = getattr(
                room,
                "region",
                None,
            )

            if region == start_zone:

                starting_room = room

                break

        if starting_room is None:

            starting_room = (
                server.world.rooms.get(1)
            )

        if starting_room is not None:

            try:

                result = (
                    starting_room.enter(
                        player
                    )
                )

                if hasattr(
                    result,
                    "__await__",
                ):

                    await result

            except Exception:

                try:

                    player.move_to(
                        starting_room
                    )

                except Exception:

                    player.room = (
                        starting_room
                    )

        # -------------------------------------------------
        # STARTING EQUIPMENT
        # -------------------------------------------------

        for vnum in CLASSES[
            class_name
        ]["start_items"]:

            prototype = (
                server.world.objects.get(
                    vnum
                )
            )

            if prototype is None:
                continue

            try:

                item = prototype.clone()

            except Exception:

                continue

            player.inventory.append(
                item
            )

        # -------------------------------------------------
        # SAVE
        # -------------------------------------------------

        from accounts import (
            save_character,
            save_account,
        )

        if name not in account.characters:

            account.characters.append(
                name
            )

        save_account(
            account
        )

        save_character(
            player
        )

        # -------------------------------------------------
        # COMPLETE
        # -------------------------------------------------

        await send()

        await send(
            "Character creation complete. "
            f"Welcome, {name}!"
        )

        return player

