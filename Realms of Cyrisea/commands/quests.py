"""
Realms of Cyrisea - Quest System
Full quest suite:
- Quest definitions
- Quest chains
- Branching quests
- Faction/guild/event quests
- Daily/weekly quests
- Quest tracking
- Quest objectives
- Quest rewards
"""

import asyncio
import logging
import random

# ---------------------------------------------------------
# Quest types
# ---------------------------------------------------------

QUEST_TYPES = [
    "story",
    "chain",
    "branch",
    "faction",
    "guild",
    "event",
    "daily",
    "weekly",
]

# ---------------------------------------------------------
# Quest registry
# ---------------------------------------------------------

QUESTS = {
    "crystalwood_intro": {
        "name": "Whispers of the Glade",
        "type": "story",
        "desc": "Investigate the strange whispers echoing through Crystalwood.",
        "objectives": [
            {"type": "go", "target": 1201, "desc": "Travel to the Crystalwood Glade."},
            {"type": "kill", "target": 9001, "count": 3, "desc": "Defeat 3 Whispering Shades."},
            {"type": "talk", "target": "Elder Thalen", "desc": "Speak with Elder Thalen."},
        ],
        "reward": {"xp": 150, "gold": 50, "item": 6001},
        "next": "crystalwood_chain_1",
    },

    "crystalwood_chain_1": {
        "name": "Heartwood Secrets",
        "type": "chain",
        "desc": "Uncover the secrets hidden within the Heartwood.",
        "objectives": [
            {"type": "collect", "target": 1101, "count": 5, "desc": "Gather 5 Red Herbs."},
            {"type": "use", "target": "Heartwood Altar", "desc": "Use the Heartwood Altar."},
        ],
        "reward": {"xp": 200, "rep": {"crystalwood": 50}},
        "next": "crystalwood_chain_2",
    },

    "crystalwood_chain_2": {
        "name": "The Heartwood Trial",
        "type": "branch",
        "desc": "Choose your path in the Heartwood Trial.",
        "branches": {
            "warden_path": {
                "desc": "Aid the Wardens in defending the glade.",
                "objectives": [
                    {"type": "kill", "target": 9002, "count": 5, "desc": "Defeat 5 Shadow Wolves."},
                ],
                "reward": {"xp": 250, "rep": {"crystalwood": 100}},
            },
            "keeper_path": {
                "desc": "Aid the Keepers in restoring the Heartwood.",
                "objectives": [
                    {"type": "collect", "target": 1103, "count": 3, "desc": "Gather 3 Blue Herbs."},
                ],
                "reward": {"xp": 250, "item": 6006},
            },
        },
        "next": None,
    },

    "obsidian_daily": {
        "name": "Arcane Sparks",
        "type": "daily",
        "desc": "Collect arcane sparks from Obsidian Wisps.",
        "objectives": [
            {"type": "collect", "target": 1201, "count": 3, "desc": "Collect 3 Arcane Dust."},
        ],
        "reward": {"xp": 50, "gold": 20},
    },

    "guild_trial": {
        "name": "Guild Trial",
        "type": "guild",
        "desc": "Prove yourself worthy of guild advancement.",
        "objectives": [
            {"type": "kill", "target": 9500, "count": 1, "desc": "Defeat the Obsidian Colossus."},
        ],
        "reward": {"xp": 300, "item": 8001},
    },

    "event_invasion": {
        "name": "Invasion Defense",
        "type": "event",
        "desc": "Defend Crystalwood from invading shadows.",
        "objectives": [
            {"type": "kill", "target": 9003, "count": 10, "desc": "Defeat 10 Shadow Fiends."},
        ],
        "reward": {"xp": 200, "rep": {"crystalwood": 50}},
    },
}

# ---------------------------------------------------------
# Player quest state
# ---------------------------------------------------------

def get_active_quests(player):
    return player.quests

def start_quest(player, quest_id):
    quest = QUESTS[quest_id]
    player.quests[quest_id] = {
        "id": quest_id,
        "progress": {},
        "branch": None,
        "completed": False,
    }

def complete_quest(player, quest_id):
    player.quests[quest_id]["completed"] = True

# ---------------------------------------------------------
# Objective tracking
# ---------------------------------------------------------

def update_objective(player, quest_id, obj_type, target):
    quest = player.quests.get(quest_id)
    if not quest or quest["completed"]:
        return

    qdef = QUESTS[quest_id]

    # Branching quests
    if qdef["type"] == "branch":
        branch = quest["branch"]
        objectives = qdef["branches"][branch]["objectives"]
    else:
        objectives = qdef["objectives"]

    for obj in objectives:
        if obj["type"] != obj_type:
            continue
        if obj["target"] != target:
            continue

        # Increment progress
        key = f"{obj_type}:{target}"
        quest["progress"][key] = quest["progress"].get(key, 0) + 1

        # Check completion
        if obj_type in ["kill", "collect"]:
            if quest["progress"][key] >= obj["count"]:
                pass  # objective complete
        else:
            quest["progress"][key] = 1  # instant objective

def quest_is_complete(player, quest_id):
    quest = player.quests[quest_id]
    qdef = QUESTS[quest_id]

    # Branching quests
    if qdef["type"] == "branch":
        branch = quest["branch"]
        objectives = qdef["branches"][branch]["objectives"]
    else:
        objectives = qdef["objectives"]

    for obj in objectives:
        key = f"{obj['type']}:{obj['target']}"
        if obj["type"] in ["kill", "collect"]:
            if quest["progress"].get(key, 0) < obj["count"]:
                return False
        else:
            if quest["progress"].get(key, 0) < 1:
                return False

    return True

# ---------------------------------------------------------
# Quest rewards
# ---------------------------------------------------------

async def grant_rewards(player, quest_id):
    qdef = QUESTS[quest_id]
    reward = qdef.get("reward", {})

    # XP
    if "xp" in reward:
        player.exp += reward["xp"]
        await player.send(f"You gain {reward['xp']} XP.")

    # Gold
    if "gold" in reward:
        player.gold += reward["gold"]
        await player.send(f"You gain {reward['gold']} gold.")

    # Item
    if "item" in reward:
        obj = player.world.objects.get(reward["item"])
        if obj:
            player.inventory.append(obj.clone())
            await player.send(f"You receive {obj.short_desc}.")

    # Faction rep
    if "rep" in reward:
        for fid, amt in reward["rep"].items():
            player.factions[fid] = player.factions.get(fid, 0) + amt
            await player.send(f"You gain {amt} reputation with {fid}.")

# ---------------------------------------------------------
# Complete quest
# ---------------------------------------------------------

async def finish_quest(player, quest_id):
    complete_quest(player, quest_id)
    await player.send(f"\033[94mQuest Complete:\033[0m {QUESTS[quest_id]['name']}")
    await grant_rewards(player, quest_id)

    # Start next quest in chain
    next_q = QUESTS[quest_id].get("next")
    if next_q:
        start_quest(player, next_q)
        await player.send(f"New quest available: {QUESTS[next_q]['name']}")

async def do_quests(player, args):
    """List active quests."""

    active = get_active_quests(player)
    if not active:
        await player.send("You have no active quests.")
        return

    await player.send("\033[95mActive Quests:\033[0m")
    for qid, q in active.items():
        qdef = QUESTS[qid]
        await player.send(f"{qdef['name']} — {qdef['desc']}")

async def do_quest(player, args):
    """Show quest details."""

    if not args:
        await player.send("Quest which?")
        return

    qid = args.lower()
    if qid not in player.quests:
        await player.send("You are not on that quest.")
        return

    qdef = QUESTS[qid]
    await player.send(f"\033[94m{qdef['name']}\033[0m")
    await player.send(qdef["desc"])

    # Branching
    if qdef["type"] == "branch":
        branch = player.quests[qid]["branch"]
        if branch:
            await player.send(f"Branch: {branch.replace('_',' ').title()}")
            objectives = qdef["branches"][branch]["objectives"]
        else:
            await player.send("Choose a branch using: questbranch <branch>")
            return
    else:
        objectives = qdef["objectives"]

    await player.send("Objectives:")
    for obj in objectives:
        await player.send(f" - {obj['desc']}")

async def do_questbranch(player, args):
    """Choose a branch in a branching quest."""

    if not args:
        await player.send("Branch which?")
        return

    # Find active branching quest
    for qid, q in player.quests.items():
        if QUESTS[qid]["type"] == "branch" and not q["branch"]:
            if args.lower() in QUESTS[qid]["branches"]:
                q["branch"] = args.lower()
                await player.send(f"You choose the {args} path.")
                return

    await player.send("No branching quest available.")

async def do_questturnin(player, args):
    """Turn in a completed quest."""

    if not args:
        await player.send("Turn in which quest?")
        return

    qid = args.lower()
    if qid not in player.quests:
        await player.send("You are not on that quest.")
        return

    if not quest_is_complete(player, qid):
        await player.send("That quest is not complete.")
        return

    await finish_quest(player, qid)

COMMAND_DEFS = [
    ("quests",      do_quests,      {"position": "standing", "help_category": "quests"}),
    ("quest",       do_quest,       {"position": "standing", "help_category": "quests"}),
    ("questbranch", do_questbranch, {"position": "standing", "help_category": "quests"}),
    ("questturnin", do_questturnin, {"position": "standing", "help_category": "quests"}),
]
