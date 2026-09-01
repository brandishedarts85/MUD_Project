"""
Realms of Cyrisea - Core Engine
Unified base classes and helpers:
- World
- Room
- Mob
- Object
- Player
- Core helper functions
"""

import asyncio
import logging
import random
import time

log = logging.getLogger(__name__)

# ---------------------------------------------------------
# Room
# ---------------------------------------------------------

class Room:
    def __init__(self, vnum, name, desc):
        self.vnum = vnum
        self.name = name
        self.desc = desc
        self.exits = {}          # direction -> {"room": Room}
        self.mobs = []           # list of Mob
        self.objects = []        # list of Object
        self.players = []        # list of Player
        self.terrain = "road"
        self.region = "crystalwood"
        self.crafting_station = None
        self.is_guildhall = False
        self.guild = None

    def add_exit(self, direction, room):
        self.exits[direction] = {"room": room}

    async def enter(self, player):
        self.players.append(player)
        player.room = self

    async def leave(self, player):
        if player in self.players:
            self.players.remove(player)

    def find_npc(self, name):
        for mob in self.mobs:
            if mob.name.lower() == name.lower():
                return mob
        return None

    def find_mob(self, name):
        return self.find_npc(name)

    def find_player(self, name):
        for p in self.players:
            if p.name.lower() == name.lower():
                return p
        return None

    def find_object(self, name):
        for obj in self.objects:
            if name.lower() in obj.short_desc.lower():
                return obj
        return None


# ---------------------------------------------------------
# Mob
# ---------------------------------------------------------

class Mob:
    def __init__(self, vnum, name):
        self.vnum = vnum
        self.name = name
        self.desc = ""
        self.level = 1
        self.hp = 100
        self.room = None
        self.respawn = False
        self.rep_gain = {}  # e.g. {"faction": ("crystalwood", 5)}

    async def send(self, msg):
        # Mobs don't receive text; stub for compatibility
        pass


# ---------------------------------------------------------
# Object
# ---------------------------------------------------------

class Object:
    def __init__(self, vnum, short_desc):
        self.vnum = vnum
        self.short_desc = short_desc
        self.desc = ""
        self.stats = {}
        self.material_type = None
        self.rune_id = None
        self.respawn = False
        self.quality = "normal"
        self.rarity = "common"
        self.sockets = 0
        self.runes = []
        self.infusions = []
        self.base_value = 10

    def clone(self):
        new = Object(self.vnum, self.short_desc)
        new.desc = self.desc
        new.stats = dict(self.stats)
        new.material_type = self.material_type
        new.rune_id = self.rune_id
        new.respawn = self.respawn
        new.quality = self.quality
        new.rarity = self.rarity
        new.sockets = self.sockets
        new.runes = list(self.runes)
        new.infusions = list(self.infusions)
        new.base_value = self.base_value
        return new


# ---------------------------------------------------------
# Corpse
# ---------------------------------------------------------

class Corpse:
    def __init__(self, owner_name, room, items, gold, decay_time, is_deadly, world):
        self.owner_name = owner_name
        self.room = room              # Room reference
        self.items = items            # list of Object or item objects
        self.gold = gold
        self.decay_time = decay_time  # timestamp when corpse should decay
        self.is_deadly = is_deadly
        self.created_at = world.now()
        self.decayed = False

    def should_decay(self, now):
        return not self.decayed and now >= self.decay_time

    def decay(self):
        # Destroy items/gold
        self.items.clear()
        self.gold = 0
        self.decayed = True


# ---------------------------------------------------------
# World
# ---------------------------------------------------------

class World:
    def __init__(self):
        self.rooms = {}          # vnum -> Room
        self.mobs = {}           # vnum -> Mob prototype
        self.objects = {}        # vnum -> Object prototype
        self.players = []        # list of Player
        self.state = {}          # worldstate module will init
        self.weather = {}        # region -> weather string
        self.active_events = {}  # event_id -> data
        self.next_instance_vnum = 100000

        # Corpses in the world
        self.corpses = []        # list of Corpse

    def now(self):
        """Unified timestamp helper."""
        return time.time()

    def create_room(self, vnum, name, desc):
        room = Room(vnum, name, desc)
        self.rooms[vnum] = room
        return room

    def create_mob(self, vnum, name):
        mob = Mob(vnum, name)
        self.mobs[vnum] = mob
        return mob

    def create_object(self, vnum, name):
        obj = Object(vnum, name)
        self.objects[vnum] = obj
        return obj

    def reload_modules(self):
        # Stub: in a real engine, this would reload command modules
        log.info("World modules reloaded (stub).")

    def find_player_global(self, name):
        for p in self.players:
            if p.name.lower() == name.lower():
                return p
        return None

    async def trigger_event(self, event_id):
        # Stub for dialogue/worldstate integration
        log.info(f"Event triggered: {event_id}")


# ---------------------------------------------------------
# Player
# ---------------------------------------------------------

class Player:
    def __init__(self, name, world):
        self.name = name
        self.world = world
        self.room = None
        self.inventory = []
        self.gold = 0
        self.exp = 0
        self.stats = {"hp": 100, "mana": 100}
        self.stamina = 100

        # Social/admin
        self.is_admin = False
        self.is_builder = False

        # PvP mode
        self.is_peaceful = True      # set at character creation
        self.is_deadly = False       # mutually exclusive with peaceful

        # Temporary hostility (for peaceful attacking deadly)
        self.is_hostile = False
        self.hostile_until = None    # timestamp when hostility expires

        # Death / corpse tracking
        self.last_death_time = None
        self.last_corpse = None      # reference to Corpse object

        # Progression penalties
        self.durability_penalty = 0
        self.fatigue = 0

        # Skill / spell / profession containers
        self.skills = {}
        self.spellbook = {}
        self.professions = {}         # name -> {level, xp, skill_nodes}
        self.travel_professions = set()
        self.fast_travel_unlocks = set()

        # Guilds
        self.guild = None
        self.guild_rank = None
        self.guild_invite = None

        # Pets
        self.pet = None
        self.pet_data = {}

        # Quests
        self.quests = {}
        self.quest_complete_count = 0

        # Achievements
        self.achievements = set()
        self.achievement_points = 0

        # Titles
        self.titles = set()
        self.active_title = None

        # Reputation & factions
        self.reputation = {}          # category -> {key -> value}
        self.factions = {}            # faction_id -> rep
        self.regions_explored = set()
        self.rooms_visited = set()

        # Dialogue
        self.dialogue_state = None

        # Travel
        self.mount = None
        self.boat = None

        # Favor (for deity interactions)
        self.favor = 0

    async def send(self, msg):
        # Replace with actual network send in real engine
        print(f"[{self.name}] {msg}")


# ---------------------------------------------------------
# Helper functions expected by other modules
# ---------------------------------------------------------

def kill_target(player, target):
    """
    Simple combat helper used by pet system.
    In a full combat module, this would be more complex.
    """
    if isinstance(target, Mob):
        target.hp = 0
        if target.room and target in target.room.mobs:
            target.room.mobs.remove(target)
        asyncio.create_task(player.send(f"You defeat {target.name}."))
    else:
        # PvP or other entities could be handled in the combat module
        asyncio.create_task(player.send("You strike your target down."))


def get_faction_rank_value(world, faction_id, rank):
    """
    Used by achievements to evaluate faction rank thresholds.
    For now, simple mapping: rank -> numeric value.
    """
    rank_values = {
        "ally": 500,
        "honored": 750,
        "exalted": 1000,
    }
    return rank_values.get(rank, 0)


# ---------------------------------------------------------
# Engine bootstrap convenience
# ---------------------------------------------------------

def create_default_world():
    """
    Create a world with minimal setup.
    Other modules (worldstate, travel, etc.) will extend it.
    """
    world = World()
    # Basic weather defaults
    world.weather = {
        "crystalwood": "clear",
        "obsidian_order": "clear",
        "sunspire": "clear",
        "frostpeak": "clear",
    }
    return world
