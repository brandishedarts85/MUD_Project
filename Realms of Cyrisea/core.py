"""
Realms of Cyrisea - Core Engine

The foundation for the MUD world.

This module defines the canonical game objects:
    World
    Room
    Exit
    Mob
    Object
    Player
    Corpse

The engine uses a VNUM/prototype architecture similar to classic MUDs:
    - World prototypes live in World.mobs / World.objects.
    - Live instances are placed into rooms or player inventories.
    - Objects and mobs can be cloned from their prototypes.

This file intentionally contains compatibility properties for older
Cyrisea modules while the rest of the project is brought onto one
consistent API.
"""

from __future__ import annotations

import time
from copy import deepcopy
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# EXIT
# ---------------------------------------------------------------------------

class Exit:
    """
    A directional connection between two rooms.

    Newer code can use:
        exit.destination

    Older code can use:
        exit["room"]

    This lets us stabilize the engine without immediately rewriting every
    movement/map module.
    """

    def __init__(
        self,
        direction: str,
        destination: Optional["Room"] = None,
        **kwargs: Any,
    ):
        self.direction = direction.lower()
        self.destination = destination

        self.closed = kwargs.get("closed", False)
        self.locked = kwargs.get("locked", False)
        self.key_vnum = kwargs.get("key_vnum")
        self.hidden = kwargs.get("hidden", False)
        self.door = kwargs.get("door", False)

    def __getitem__(self, key: str) -> Any:
        if key == "room":
            return self.destination

        if key == "destination":
            return self.destination

        if key == "direction":
            return self.direction

        if key == "closed":
            return self.closed

        if key == "locked":
            return self.locked

        if key == "key_vnum":
            return self.key_vnum

        if key == "hidden":
            return self.hidden

        if key == "door":
            return self.door

        raise KeyError(key)

    def __setitem__(self, key: str, value: Any) -> None:
        if key in ("room", "destination"):
            self.destination = value
            return

        if key == "direction":
            self.direction = str(value).lower()
            return

        if key == "closed":
            self.closed = bool(value)
            return

        if key == "locked":
            self.locked = bool(value)
            return

        if key == "key_vnum":
            self.key_vnum = value
            return

        if key == "hidden":
            self.hidden = bool(value)
            return

        if key == "door":
            self.door = bool(value)
            return

        raise KeyError(key)

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def __contains__(self, key: str) -> bool:
        return key in {
            "room",
            "destination",
            "direction",
            "closed",
            "locked",
            "key_vnum",
            "hidden",
            "door",
        }

    def __repr__(self) -> str:
        destination = (
            self.destination.vnum
            if self.destination is not None
            else None
        )

        return (
            f"<Exit direction={self.direction!r} "
            f"destination={destination!r}>"
        )


# ---------------------------------------------------------------------------
# ROOM
# ---------------------------------------------------------------------------

class Room:
    """
    A live room in the world.

    Rooms are identified by VNUM.

    Compatibility:
        desc <-> description
        terrain <-> sector
        objects <-> items
    """

    def __init__(
        self,
        vnum: int,
        name: str = "An Unnamed Room",
        desc: str = "",
        terrain: str = "road",
        region: str = "crystalwood",
        **kwargs: Any,
    ):
        self.vnum = int(vnum)
        self.name = name

        self._description = desc

        self.exits: Dict[str, Exit] = {}

        self.mobs: List[Mob] = []
        self.objects: List[Object] = []
        self.players: List[Player] = []

        self._terrain = terrain
        self.region = region

        self.area = kwargs.get("area", region)
        self.coord = kwargs.get("coord")

        self.crafting_station = kwargs.get("crafting_station")
        self.is_guildhall = kwargs.get("is_guildhall", False)
        self.guild = kwargs.get("guild")

        self.flags = kwargs.get("flags", set())

    @property
    def desc(self) -> str:
        return self._description

    @desc.setter
    def desc(self, value: str) -> None:
        self._description = value

    @property
    def description(self) -> str:
        return self._description

    @description.setter
    def description(self, value: str) -> None:
        self._description = value

    @property
    def terrain(self) -> str:
        return self._terrain

    @terrain.setter
    def terrain(self, value: str) -> None:
        self._terrain = value

    @property
    def sector(self) -> str:
        return self._terrain

    @sector.setter
    def sector(self, value: str) -> None:
        self._terrain = value

    @property
    def items(self) -> List["Object"]:
        return self.objects

    @items.setter
    def items(self, value: List["Object"]) -> None:
        self.objects = value

    def add_exit(
        self,
        direction: str,
        destination: "Room",
        **kwargs: Any,
    ) -> Exit:
        direction = direction.lower()

        exit_obj = Exit(
            direction=direction,
            destination=destination,
            **kwargs,
        )

        self.exits[direction] = exit_obj
        return exit_obj

    def remove_exit(self, direction: str) -> None:
        self.exits.pop(direction.lower(), None)

    def get_exit(self, direction: str) -> Optional[Exit]:
        return self.exits.get(direction.lower())

    def enter(self, player: "Player") -> None:
        if player.room is self:
            if player not in self.players:
                self.players.append(player)
            return

        if player.room is not None:
            player.room.leave(player)

        player.room = self

        if player not in self.players:
            self.players.append(player)

    def leave(self, player: "Player") -> None:
        if player in self.players:
            self.players.remove(player)

        if player.room is self:
            player.room = None

    def add_mob(self, mob: "Mob") -> None:
        if mob.room is not None and mob.room is not self:
            mob.room.remove_mob(mob)

        mob.room = self

        if mob not in self.mobs:
            self.mobs.append(mob)

    def remove_mob(self, mob: "Mob") -> None:
        if mob in self.mobs:
            self.mobs.remove(mob)

        if mob.room is self:
            mob.room = None

    def add_object(self, obj: "Object") -> None:
        if obj.room is not None and obj.room is not self:
            obj.room.remove_object(obj)

        obj.room = self

        if obj not in self.objects:
            self.objects.append(obj)

    def remove_object(self, obj: "Object") -> None:
        if obj in self.objects:
            self.objects.remove(obj)

        if obj.room is self:
            obj.room = None

    def find_npc(self, name: str) -> Optional["Mob"]:
        name = name.lower()

        for mob in self.mobs:
            if mob.name.lower() == name:
                return mob

        for mob in self.mobs:
            if name in mob.name.lower():
                return mob

        return None

    def find_mob(self, name: str) -> Optional["Mob"]:
        return self.find_npc(name)

    def find_player(self, name: str) -> Optional["Player"]:
        name = name.lower()

        for player in self.players:
            if player.name.lower() == name:
                return player

        for player in self.players:
            if name in player.name.lower():
                return player

        return None

    def find_object(self, name: str) -> Optional["Object"]:
        name = name.lower()

        for obj in self.objects:
            if obj.matches_name(name):
                return obj

        return None

    def broadcast(
        self,
        message: str,
        exclude: Optional["Player"] = None,
    ) -> None:
        for player in list(self.players):
            if player is exclude:
                continue

            player.send(message)

    def __repr__(self) -> str:
        return f"<Room {self.vnum}: {self.name!r}>"


# ---------------------------------------------------------------------------
# MOB
# ---------------------------------------------------------------------------

class Mob:
    """
    A mobile/NPC prototype or live mob instance.
    """

    def __init__(
        self,
        vnum: int,
        name: str,
        desc: str = "",
        level: int = 1,
        hp: Optional[int] = None,
        **kwargs: Any,
    ):
        self.vnum = int(vnum)

        self.name = name
        self._description = desc

        self.level = int(level)

        self.max_hp = int(
            kwargs.get(
                "max_hp",
                hp if hp is not None else max(10, level * 10),
            )
        )

        self.hp = int(
            hp if hp is not None else self.max_hp
        )

        self.room: Optional[Room] = None

        self.respawn = kwargs.get("respawn", True)
        self.respawn_point = kwargs.get("respawn_point")

        self.rep_gain = kwargs.get("rep_gain", 0)

        self.vnum_prototype = kwargs.get("vnum_prototype", self.vnum)

        self.is_npc = True
        self.fighting = None
        self.effects: Dict[str, Any] = {}

        self.stats = kwargs.get("stats", {})

    @property
    def desc(self) -> str:
        return self._description

    @desc.setter
    def desc(self, value: str) -> None:
        self._description = value

    @property
    def long_desc(self) -> str:
        return self._description

    @long_desc.setter
    def long_desc(self, value: str) -> None:
        self._description = value

    @property
    def short_desc(self) -> str:
        return self.name

    @short_desc.setter
    def short_desc(self, value: str) -> None:
        self.name = value

    async def send(self, message: str) -> None:
        print(f"[{self.name}] {message}")

    def clone(self) -> "Mob":
        clone = deepcopy(self)

        clone.room = None
        clone.fighting = None
        clone.hp = clone.max_hp
        clone.vnum_prototype = self.vnum

        return clone

    def spawn(self, room: Room) -> "Mob":
        mob = self.clone()
        room.add_mob(mob)
        return mob

    def __repr__(self) -> str:
        return f"<Mob {self.vnum}: {self.name!r}>"


# ---------------------------------------------------------------------------
# OBJECT
# ---------------------------------------------------------------------------

class Object:
    """
    Item/object prototype or live item instance.

    Compatibility:
        short_desc <-> name
        desc <-> long_desc
        base_value <-> value
    """

    def __init__(
        self,
        vnum: int,
        short_desc: str,
        desc: str = "",
        stats: Optional[Dict[str, Any]] = None,
        material_type: str = "generic",
        **kwargs: Any,
    ):
        self.vnum = int(vnum)

        self._name = short_desc
        self._description = desc

        self.stats: Dict[str, Any] = (
            deepcopy(stats)
            if stats is not None
            else {}
        )

        self.material_type = material_type

        self.rune_id = kwargs.get("rune_id")
        self.respawn = kwargs.get("respawn", False)

        self.quality = kwargs.get("quality", "common")
        self.rarity = kwargs.get("rarity", "common")

        self.sockets = deepcopy(
            kwargs.get("sockets", [])
        )

        self.runes = deepcopy(
            kwargs.get("runes", [])
        )

        self.infusions = deepcopy(
            kwargs.get("infusions", [])
        )

        self.base_value = kwargs.get(
            "base_value",
            kwargs.get("value", 0),
        )

        self.value = self.base_value

        self.weight = kwargs.get("weight", 1)

        self.type = kwargs.get(
            "type",
            kwargs.get("item_type", "misc"),
        )

        self.item_type = self.type

        self.bonuses = deepcopy(
            kwargs.get("bonuses", {})
        )

        self.consumable = kwargs.get(
            "consumable",
            False,
        )

        self.use_effect = kwargs.get(
            "use_effect"
        )

        self.stackable = kwargs.get(
            "stackable",
            False,
        )

        self.quantity = kwargs.get(
            "quantity",
            1,
        )

        self.tags = set(
            kwargs.get("tags", [])
        )

        self.material = kwargs.get(
            "material",
            material_type,
        )

        self.durability = kwargs.get(
            "durability",
            100,
        )

        self.max_durability = kwargs.get(
            "max_durability",
            self.durability,
        )

        self.owner = kwargs.get("owner")

        self.room: Optional[Room] = None

        self.vnum_prototype = kwargs.get(
            "vnum_prototype",
            self.vnum,
        )

        self.equipped = kwargs.get(
            "equipped",
            False,
        )

    @property
    def short_desc(self) -> str:
        return self._name

    @short_desc.setter
    def short_desc(self, value: str) -> None:
        self._name = value

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value

    @property
    def desc(self) -> str:
        return self._description

    @desc.setter
    def desc(self, value: str) -> None:
        self._description = value

    @property
    def long_desc(self) -> str:
        return self._description

    @long_desc.setter
    def long_desc(self, value: str) -> None:
        self._description = value

    @property
    def base_value(self) -> int:
        return self._base_value

    @base_value.setter
    def base_value(self, value: Any) -> None:
        try:
            self._base_value = int(value)
        except (TypeError, ValueError):
            self._base_value = 0

    @property
    def value(self) -> int:
        return self._base_value

    @value.setter
    def value(self, value: Any) -> None:
        self.base_value = value

    def matches_name(self, query: str) -> bool:
        query = query.lower().strip()

        if not query:
            return False

        return (
            query == self.name.lower()
            or query in self.name.lower()
        )

    def colored_name(self) -> str:
        return self.name

    def use(self, player: "Player") -> bool:
        return False

    def clone(self) -> "Object":
        clone = deepcopy(self)

        clone.room = None
        clone.owner = None
        clone.equipped = False
        clone.vnum_prototype = self.vnum

        return clone

    def __repr__(self) -> str:
        return f"<Object {self.vnum}: {self.name!r}>"


# ---------------------------------------------------------------------------
# CORPSE
# ---------------------------------------------------------------------------

class Corpse:
    """
    A player's corpse.

    Corpses contain item instances and gold and decay after a defined
    amount of time.
    """

    def __init__(
        self,
        owner_name: str,
        room: Optional[Room] = None,
        items: Optional[List[Object]] = None,
        gold: int = 0,
        decay_time: int = 1800,
        is_deadly: bool = False,
        world: Optional["World"] = None,
    ):
        self.owner_name = owner_name

        self.room = room
        self.items: List[Object] = (
            items if items is not None else []
        )

        self.gold = int(gold)
        self.decay_time = int(decay_time)
        self.is_deadly = is_deadly

        self.created_at = (
            world.now()
            if world is not None
            else time.time()
        )

        self.decayed = False

    @property
    def expires_at(self) -> float:
        return self.created_at + self.decay_time

    def is_expired(
        self,
        current_time: Optional[float] = None,
    ) -> bool:
        if self.decayed:
            return True

        if current_time is None:
            current_time = time.time()

        return current_time >= self.expires_at

    def decay(self) -> None:
        self.items.clear()
        self.gold = 0
        self.decayed = True

    def __repr__(self) -> str:
        return (
            f"<Corpse owner={self.owner_name!r} "
            f"gold={self.gold} items={len(self.items)}>"
        )


# ---------------------------------------------------------------------------
# WORLD
# ---------------------------------------------------------------------------

class World:
    """
    The central world container.

    The World owns:
        rooms
        mob prototypes
        object prototypes
        connected players
        world state
        weather
        events
        corpses
    """

    def __init__(self):
        self.rooms: Dict[int, Room] = {}
        self.mobs: Dict[int, Mob] = {}
        self.objects: Dict[int, Object] = {}
        self.players: List[Player] = []

        self.state: Dict[str, Any] = {}

        self.weather: Dict[str, Any] = {}

        self.active_events: Dict[str, Any] = {}

        self.corpses: List[Corpse] = []

        self.next_instance_vnum = 100000

        self.running = True

        self.factions: Dict[str, Any] = {}
        self.quests: Dict[str, Any] = {}

        self.weather_effects: Dict[str, Any] = {}

        self.trade_routes: Dict[str, Any] = {}
        self.auctions: Dict[str, Any] = {}

        self.tax_rate = 0.0

        self.supply_demand: Dict[str, Any] = {}

        self.server = None

    @staticmethod
    def now() -> float:
        return time.time()

    def create_room(
        self,
        vnum: int,
        name: str = "An Unnamed Room",
        desc: str = "",
        **kwargs: Any,
    ) -> Room:
        room = Room(
            vnum=vnum,
            name=name,
            desc=desc,
            **kwargs,
        )

        self.rooms[int(vnum)] = room
        return room

    def create_mob(
        self,
        vnum: int,
        name: str,
        desc: str = "",
        level: int = 1,
        hp: Optional[int] = None,
        **kwargs: Any,
    ) -> Mob:
        mob = Mob(
            vnum=vnum,
            name=name,
            desc=desc,
            level=level,
            hp=hp,
            **kwargs,
        )

        self.mobs[int(vnum)] = mob
        return mob

    def create_object(
        self,
        vnum: int,
        short_desc: str,
        desc: str = "",
        stats: Optional[Dict[str, Any]] = None,
        material_type: str = "generic",
        **kwargs: Any,
    ) -> Object:
        obj = Object(
            vnum=vnum,
            short_desc=short_desc,
            desc=desc,
            stats=stats,
            material_type=material_type,
            **kwargs,
        )

        self.objects[int(vnum)] = obj
        return obj

    def allocate_instance_vnum(self) -> int:
        vnum = self.next_instance_vnum
        self.next_instance_vnum += 1
        return vnum

    def add_player(self, player: "Player") -> None:
        if player not in self.players:
            self.players.append(player)

        player.world = self

    def remove_player(self, player: "Player") -> None:
        if player in self.players:
            self.players.remove(player)

        if player.room is not None:
            player.room.leave(player)

    def find_player_global(
        self,
        name: str,
    ) -> Optional["Player"]:
        name = name.lower().strip()

        if not name:
            return None

        for player in self.players:
            if player.name.lower() == name:
                return player

        for player in self.players:
            if name in player.name.lower():
                return player

        return None

    def get_faction_rank_value(
        self,
        faction_id: str,
        rank: str,
    ) -> int:
        faction = self.factions.get(faction_id)

        if not faction:
            return 0

        ranks = faction.get("ranks", {}) if isinstance(
            faction,
            dict,
        ) else getattr(faction, "ranks", {})

        rank_data = ranks.get(rank)

        if rank_data is None:
            return 0

        if isinstance(rank_data, dict):
            return int(
                rank_data.get(
                    "value",
                    rank_data.get("min_rep", 0),
                )
            )

        if isinstance(rank_data, (int, float)):
            return int(rank_data)

        return 0

    def reload_modules(self) -> None:
        return None

    def trigger_event(
        self,
        event_id: str,
        **kwargs: Any,
    ) -> Any:
        try:
            from events import trigger_event

            return trigger_event(
                self,
                event_id,
                **kwargs,
            )
        except (ImportError, AttributeError, TypeError):
            return None

    def add_corpse(self, corpse: Corpse) -> None:
        if corpse not in self.corpses:
            self.corpses.append(corpse)

    def remove_corpse(self, corpse: Corpse) -> None:
        if corpse in self.corpses:
            self.corpses.remove(corpse)

    def process_corpses(self) -> None:
        current_time = self.now()

        for corpse in list(self.corpses):
            if corpse.is_expired(current_time):
                corpse.decay()
                self.corpses.remove(corpse)

    def shutdown(self) -> None:
        self.running = False

    def __repr__(self) -> str:
        return (
            f"<World rooms={len(self.rooms)} "
            f"mobs={len(self.mobs)} "
            f"objects={len(self.objects)} "
            f"players={len(self.players)}>"
        )


# ---------------------------------------------------------------------------
# PLAYER
# ---------------------------------------------------------------------------

class Player:
    """
    A player character.

    The Player deliberately contains the broad state that the existing
    Cyrisea systems already expect. Systems such as quests, factions,
    crafting, guilds, pets, housing, titles, etc. can progressively become
    more formalized without breaking the basic character object.
    """

    def __init__(
        self,
        name: str,
        world: Optional[World] = None,
        race: str = "human",
        class_name: str = "warrior",
        appearance: Optional[Dict[str, Any]] = None,
        stats: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ):
        self.name = name

        self.world = world
        self.room: Optional[Room] = None

        self.race = race
        self.class_name = class_name

        self.appearance = (
            deepcopy(appearance)
            if appearance is not None
            else {}
        )

        # --------------------------------------------------------------
        # Character attributes/resources
        # --------------------------------------------------------------

        self.stats: Dict[str, Any] = {
            "level": 1,
            "hp": 100,
            "max_hp": 100,
            "mana": 100,
            "max_mana": 100,
            "stamina": 100,
            "max_stamina": 100,
        }

        if stats:
            self.stats.update(deepcopy(stats))

        # --------------------------------------------------------------
        # Economy/progression
        # --------------------------------------------------------------

        self.gold = int(kwargs.get("gold", 0))
        self.exp = int(kwargs.get("exp", 0))
        self.favor = int(kwargs.get("favor", 0))

        # --------------------------------------------------------------
        # Inventory/equipment
        # --------------------------------------------------------------

        self.inventory: List[Object] = []

        self.equipment: Dict[str, Optional[Object]] = {}

        # --------------------------------------------------------------
        # Combat
        # --------------------------------------------------------------

        self.fighting = None
        self.target = None

        self.effects: Dict[str, Any] = {}

        self.skill_cds: Dict[str, float] = {}
        self.spell_cds: Dict[str, float] = {}

        self.skills: Dict[str, Any] = {}
        self.spellbook: Dict[str, Any] = {}

        # --------------------------------------------------------------
        # Character state
        # --------------------------------------------------------------

        self.admin = bool(kwargs.get("admin", False))
        self.builder = bool(kwargs.get("builder", False))

        self.pvp_enabled = bool(
            kwargs.get("pvp_enabled", False)
        )

        self.pvp_peaceful = bool(
            kwargs.get("pvp_peaceful", True)
        )

        self.pvp_deadly = bool(
            kwargs.get("pvp_deadly", False)
        )

        # Hostility state used by the PvP subsystem.
        self.is_hostile = bool(
            kwargs.get("is_hostile", False)
        )

        self.hostile_until = kwargs.get(
            "hostile_until"
        )

        self.durability_penalty = int(
            kwargs.get("durability_penalty", 0)
        )

        self.fatigue = int(
            kwargs.get("fatigue", 0)
        )

        self.last_death_time = kwargs.get(
            "last_death_time"
        )

        self.last_corpse = None

        # --------------------------------------------------------------
        # Professions
        # --------------------------------------------------------------

        self.professions: Dict[str, Any] = {}

        self.travel_professions: Dict[str, Any] = {}

        self.fast_travel_unlocks: set = set()

        # --------------------------------------------------------------
        # Factions / reputation
        # --------------------------------------------------------------

        self.factions: Dict[str, int] = {}

        self.reputation: Dict[str, Any] = {}

        # --------------------------------------------------------------
        # Quests
        # --------------------------------------------------------------

        self.quests: Dict[str, Any] = {}

        # --------------------------------------------------------------
        # Achievements / titles
        # --------------------------------------------------------------

        self.achievements: set = set()
        self.achievement_points = 0

        self.titles: set = set()
        self.active_title = None

        # --------------------------------------------------------------
        # Exploration/world state
        # --------------------------------------------------------------

        self.regions_explored: set = set()
        self.rooms_visited: set = set()
        self.discovered: set = set()

        self.dialogue_state = {}

        # --------------------------------------------------------------
        # Guild
        # --------------------------------------------------------------

        self.guild = None
        self.guild_rank = None
        self.guild_invite = None

        # --------------------------------------------------------------
        # Pets
        # --------------------------------------------------------------

        self.pet = None
        self.pet_data: Dict[str, Any] = {}

        # --------------------------------------------------------------
        # Housing
        # --------------------------------------------------------------

        self.home = None

        # --------------------------------------------------------------
        # Travel
        # --------------------------------------------------------------

        self.mount = None
        self.boat = None

        # --------------------------------------------------------------
        # Social systems
        # --------------------------------------------------------------

        self.friends: set = set()
        self.ignored: set = set()

        self.following = None
        self.party = None
        self.party_invite = None

        self.last_tell = None

        self.global_on = True
        self.ooc_on = True
        self.rp_on = True

        # --------------------------------------------------------------
        # Miscellaneous
        # --------------------------------------------------------------

        self.account_name = kwargs.get(
            "account_name"
        )

        self.session = kwargs.get("session")

        self.online = bool(
            kwargs.get("online", False)
        )

    # ==================================================================
    # Common Player compatibility properties
    # ==================================================================

    @property
    def level(self) -> int:
        return int(self.stats.get("level", 1))

    @level.setter
    def level(self, value: int) -> None:
        self.stats["level"] = int(value)

    @property
    def cls(self) -> str:
        return self.class_name

    @cls.setter
    def cls(self, value: str) -> None:
        self.class_name = value

    # ------------------------------------------------------------------
    # HP
    # ------------------------------------------------------------------

    @property
    def hp(self) -> int:
        return int(self.stats.get("hp", 0))

    @hp.setter
    def hp(self, value: int) -> None:
        self.stats["hp"] = max(0, int(value))

    @property
    def max_hp(self) -> int:
        return int(
            self.stats.get(
                "max_hp",
                self.stats.get("hp", 100),
            )
        )

    @max_hp.setter
    def max_hp(self, value: int) -> None:
        self.stats["max_hp"] = max(1, int(value))

    # ------------------------------------------------------------------
    # Mana
    # ------------------------------------------------------------------

    @property
    def mana(self) -> int:
        return int(self.stats.get("mana", 0))

    @mana.setter
    def mana(self, value: int) -> None:
        self.stats["mana"] = max(0, int(value))

    @property
    def max_mana(self) -> int:
        return int(
            self.stats.get(
                "max_mana",
                self.stats.get("mana", 100),
            )
        )

    @max_mana.setter
    def max_mana(self, value: int) -> None:
        self.stats["max_mana"] = max(1, int(value))

    # ------------------------------------------------------------------
    # Stamina
    # ------------------------------------------------------------------

    @property
    def stamina(self) -> int:
        return int(self.stats.get("stamina", 0))

    @stamina.setter
    def stamina(self, value: int) -> None:
        self.stats["stamina"] = max(0, int(value))

    @property
    def max_stamina(self) -> int:
        return int(
            self.stats.get(
                "max_stamina",
                self.stats.get("stamina", 100),
            )
        )

    @max_stamina.setter
    def max_stamina(self, value: int) -> None:
        self.stats["max_stamina"] = max(1, int(value))

    # ------------------------------------------------------------------
    # Fatigue/exhaustion compatibility
    # ------------------------------------------------------------------

    @property
    def exhaustion(self) -> int:
        return self.fatigue

    @exhaustion.setter
    def exhaustion(self, value: int) -> None:
        self.fatigue = int(value)

    # ==================================================================
    # Messaging
    # ==================================================================

    def send(self, message: str) -> None:
        if self.session is not None:
            session_send = getattr(
                self.session,
                "send",
                None,
            )

            if callable(session_send):
                try:
                    result = session_send(message)

                    if hasattr(result, "__await__"):
                        pass

                    return

                except Exception:
                    pass

        print(f"[{self.name}] {message}")

    # ==================================================================
    # Room movement
    # ==================================================================

    def move_to(self, room: Optional[Room]) -> None:
        if room is None:
            if self.room is not None:
                self.room.leave(self)
            else:
                self.room = None

            return

        room.enter(self)

    # ==================================================================
    # Inventory
    # ==================================================================

    def add_inventory(self, obj: Object) -> None:
        if obj.room is not None:
            obj.room.remove_object(obj)

        obj.room = None

        if obj not in self.inventory:
            self.inventory.append(obj)

    def remove_inventory(self, obj: Object) -> None:
        if obj in self.inventory:
            self.inventory.remove(obj)

    def find_inventory_object(
        self,
        name: str,
    ) -> Optional[Object]:
        name = name.lower()

        for obj in self.inventory:
            if obj.matches_name(name):
                return obj

        return None

    # ==================================================================
    # Player lookup
    # ==================================================================

    def find_player_global(
        self,
        name: str,
    ) -> Optional["Player"]:
        if self.world is None:
            return None

        return self.world.find_player_global(name)

    def get_all_players(self) -> List["Player"]:
        if self.world is None:
            return []

        return list(self.world.players)

    # ==================================================================
    # Effects
    # ==================================================================

    def add_status(
        self,
        status: str,
        duration: Optional[float] = None,
        magnitude: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        self.effects[status] = {
            "duration": duration,
            "magnitude": magnitude,
            **kwargs,
        }

    def remove_status(self, status: str) -> None:
        self.effects.pop(status, None)

    def has_status(self, status: str) -> bool:
        return status in self.effects

    # ==================================================================
    # Factions
    # ==================================================================

    def get_faction_reputation(
        self,
        faction_id: str,
    ) -> int:
        return int(
            self.factions.get(
                faction_id,
                0,
            )
        )

    def modify_faction_reputation(
        self,
        faction_id: str,
        amount: int,
    ) -> int:
        new_value = (
            self.get_faction_reputation(faction_id)
            + int(amount)
        )

        self.factions[faction_id] = new_value

        return new_value

    # ==================================================================
    # Combat
    # ==================================================================

    def kill_target(self, target: Any) -> None:
        try:
            from combat import kill_target

            kill_target(self, target)
            return

        except (ImportError, AttributeError, TypeError):
            pass

        if hasattr(target, "hp"):
            target.hp = 0

    # ==================================================================
    # Prototype helpers
    # ==================================================================

    def clone_object_from_world(
        self,
        vnum: int,
    ) -> Optional[Object]:
        if self.world is None:
            return None

        prototype = self.world.objects.get(int(vnum))

        if prototype is None:
            return None

        return prototype.clone()

    # ==================================================================
    # Utility
    # ==================================================================

    def get_display_name(self) -> str:
        if self.active_title:
            return f"{self.name} [{self.active_title}]"

        return self.name

    def __repr__(self) -> str:
        return (
            f"<Player {self.name!r} "
            f"level={self.level} "
            f"race={self.race!r} "
            f"class={self.class_name!r}>"
        )


# ---------------------------------------------------------------------------
# DEFAULT WORLD
# ---------------------------------------------------------------------------

def create_default_world() -> World:
    """
    Create the initial Cyrisea world.

    This intentionally remains small. The Builder/OLC system will eventually
    be responsible for building out the actual sprawling world.
    """

    world = World()

    # --------------------------------------------------------------
    # Starting room
    # --------------------------------------------------------------

    clearing = world.create_room(
        1,
        "Quiet Clearing",
        "You are in a quiet clearing. Paths lead north and east.",
        terrain="road",
        region="crystalwood",
    )

    forest = world.create_room(
        2,
        "Crystalwood Forest",
        "Tall trees surround you. The clearing lies south.",
        terrain="forest",
        region="crystalwood",
    )

    river = world.create_room(
        3,
        "Crystal River",
        "A clear river flows steadily past the edge of the forest.",
        terrain="water",
        region="crystalwood",
    )

    # --------------------------------------------------------------
    # Connections
    # --------------------------------------------------------------

    clearing.add_exit("north", forest)
    clearing.add_exit("east", river)

    forest.add_exit("south", clearing)
    river.add_exit("west", clearing)

    # --------------------------------------------------------------
    # Basic regional weather
    # --------------------------------------------------------------

    world.weather["crystalwood"] = "clear"

    # --------------------------------------------------------------
    # Initial world state
    # --------------------------------------------------------------

    world.state = {
        "global": {
            "day": 1,
            "season": "spring",
            "magic_level": 1.0,
            "world_tension": 0,
            "faction_war": False,
        },
        "regions": {
            "crystalwood": {
                "weather_bias": "clear",
            }
        },
    }

    return world