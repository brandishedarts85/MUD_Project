"""
Realms of Cyrisea - Weather System
Full weather suite:
- Dynamic weather
- Regional climate patterns
- Storms, fog, snow
- Magical auroras
- Weather effects on gameplay
- Weather forecasting
"""

import random
import asyncio


# ---------------------------------------------------------
# Regional climate definitions
# ---------------------------------------------------------

CLIMATES = {
    "crystalwood": {
        "region": "Crystalwood Glade",
        "patterns": ["clear", "fog", "rain", "arcane_aurora"],
        "temp_range": (50, 75),
    },
    "obsidian_order": {
        "region": "Obsidian Highlands",
        "patterns": ["clear", "storm", "arcane_storm"],
        "temp_range": (40, 65),
    },
    "sunspire": {
        "region": "Sunspire Coast",
        "patterns": ["clear", "rain", "wind"],
        "temp_range": (60, 85),
    },
    "frostpeak": {
        "region": "Frostpeak Mountains",
        "patterns": ["clear", "snow", "blizzard"],
        "temp_range": (10, 35),
    },
}


# ---------------------------------------------------------
# Weather effects
# ---------------------------------------------------------

WEATHER_EFFECTS = {
    "clear": {
        "desc": "The skies are clear.",
        "movement_mod": 1.0,
        "combat_mod": 1.0,
        "map_visibility": 1.0,
    },
    "fog": {
        "desc": "A thick fog blankets the land.",
        "movement_mod": 0.9,
        "combat_mod": 0.95,
        "map_visibility": 0.5,
    },
    "rain": {
        "desc": "Rain falls steadily.",
        "movement_mod": 0.9,
        "combat_mod": 1.0,
        "map_visibility": 0.8,
    },
    "storm": {
        "desc": "A violent storm rages overhead.",
        "movement_mod": 0.7,
        "combat_mod": 0.9,
        "map_visibility": 0.6,
    },
    "snow": {
        "desc": "Snow drifts gently across the land.",
        "movement_mod": 0.85,
        "combat_mod": 1.0,
        "map_visibility": 0.7,
    },
    "blizzard": {
        "desc": "A blizzard howls with icy fury.",
        "movement_mod": 0.6,
        "combat_mod": 0.9,
        "map_visibility": 0.3,
    },
    "wind": {
        "desc": "Strong coastal winds blow inland.",
        "movement_mod": 0.95,
        "combat_mod": 1.0,
        "map_visibility": 0.9,
    },
    "arcane_aurora": {
        "desc": "A shimmering aurora fills the sky with magic.",
        "movement_mod": 1.0,
        "combat_mod": 1.1,
        "mana_regen": 2.0,
        "map_visibility": 1.0,
    },
    "arcane_storm": {
        "desc": "Crackling arcane lightning splits the sky.",
        "movement_mod": 0.8,
        "combat_mod": 1.2,
        "mana_regen": 1.5,
        "map_visibility": 0.7,
    },
}


# ---------------------------------------------------------
# Weather state per region
# ---------------------------------------------------------

def get_region_weather(world, region):
    return world.weather.get(region, {"type": "clear", "temp": 70})


def set_region_weather(world, region, weather_type, temp):
    world.weather[region] = {"type": weather_type, "temp": temp}


# ---------------------------------------------------------
# Weather generation
# ---------------------------------------------------------

def generate_weather(region_id):
    climate = CLIMATES[region_id]
    weather_type = random.choice(climate["patterns"])
    temp = random.randint(*climate["temp_range"])
    return weather_type, temp


async def weather_tick(world):
    """Periodic weather update (called by server weather_task)."""

    for region_id, climate in CLIMATES.items():
        weather_type, temp = generate_weather(region_id)
        set_region_weather(world, region_id, weather_type, temp)

        # Notify players in region
        for p in world.players:
            if getattr(p.room, "region", None) == region_id:
                effect = WEATHER_EFFECTS[weather_type]
                await p.send(f"\033[94mWeather Update:\033[0m {effect['desc']}")


# ---------------------------------------------------------
# Player weather commands
# ---------------------------------------------------------

async def do_weather(player, args):
    """Show current weather."""

    region = getattr(player.room, "region", None)
    if not region:
        await player.send("This area has no weather data.")
        return

    state = get_region_weather(player.world, region)
    effect = WEATHER_EFFECTS[state["type"]]

    await player.send(f"\033[94mWeather in {CLIMATES[region]['region']}:\033[0m")
    await player.send(f"Condition: {state['type'].replace('_', ' ').title()}")
    await player.send(f"Temperature: {state['temp']}°F")
    await player.send(effect["desc"])


async def do_forecast(player, args):
    """Show possible weather patterns for this region."""

    region = getattr(player.room, "region", None)
    if not region:
        await player.send("This area has no weather data.")
        return

    patterns = CLIMATES[region]["patterns"]

    await player.send(f"\033[95mForecast for {CLIMATES[region]['region']}:\033[0m")
    for p in patterns:
        await player.send(f" - {p.replace('_', ' ').title()}")


# ---------------------------------------------------------
# Command definitions
# ---------------------------------------------------------

COMMAND_DEFS = [
    ("weather",  do_weather,  {"position": "standing", "help_category": "weather"}),
    ("forecast", do_forecast, {"position": "standing", "help_category": "weather"}),
]
