"""
Realms of Cyrisea - Dialogue System
Full dialogue suite:
- NPC dialogue trees
- Branching dialogue
- Reputation-based dialogue
- Quest-based dialogue
- Event-based dialogue
- Faction/guild dialogue
- Dialogue choices
- Dialogue consequences
"""

import asyncio
import logging
import random

# ---------------------------------------------------------
# Dialogue node structure
# ---------------------------------------------------------

# Each NPC has:
# npc.dialogue_tree = {
#     "start": {
#         "text": "...",
#         "choices": {
#             "Ask about the forest": "forest_info",
#             "Ask about the Heartwood": "heartwood_info",
#         }
#     },
#     "forest_info": {
#         "text": "...",
#         "choices": {...}
#     },
#     ...
# }

# Dialogue nodes can also have:
# - reputation gates
# - quest gates
# - faction/guild gates
# - event gates
# - consequences

# ---------------------------------------------------------
# Dialogue conditions
# ---------------------------------------------------------

def check_conditions(player, node):
    """Check if player meets dialogue conditions."""

    # Reputation gate
    if "rep_gate" in node:
        cat, key, min_rep = node["rep_gate"]
        rep = player.reputation.get(cat, {}).get(key, 0)
        if rep < min_rep:
            return False

    # Quest gate
    if "quest_gate" in node:
        qid = node["quest_gate"]
        if qid not in player.quests:
            return False

    # Faction gate
    if "faction_gate" in node:
        fid, min_rep = node["faction_gate"]
        if player.factions.get(fid, 0) < min_rep:
            return False

    # Guild gate
    if "guild_gate" in node:
        rank = node["guild_gate"]
        if player.guild_rank != rank:
            return False

    # Event gate
    if "event_gate" in node:
        eid = node["event_gate"]
        if eid not in player.world.active_events:
            return False

    return True

# ---------------------------------------------------------
# Dialogue consequences
# ---------------------------------------------------------

async def apply_consequences(player, npc, node):
    """Apply consequences of dialogue choices."""

    cons = node.get("consequence")
    if not cons:
        return

    # Reputation change
    if "rep" in cons:
        cat, key, amt = cons["rep"]
        player.reputation.setdefault(cat, {})
        player.reputation[cat][key] = player.reputation[cat].get(key, 0) + amt
        await player.send(f"Your reputation with {key} changes by {amt}.")

    # Quest start
    if "start_quest" in cons:
        qid = cons["start_quest"]
        player.quests[qid] = {"id": qid, "progress": {}, "completed": False}
        await player.send(f"New quest started: {player.world.quests[qid]['name']}")

    # Quest progress
    if "quest_progress" in cons:
        qid, obj_type, target = cons["quest_progress"]
        from commands.quests import update_objective
        update_objective(player, qid, obj_type, target)

    # Give item
    if "item" in cons:
        obj = player.world.objects.get(cons["item"])
        if obj:
            player.inventory.append(obj.clone())
            await player.send(f"You receive {obj.short_desc}.")

    # Trigger event
    if "trigger_event" in cons:
        eid = cons["trigger_event"]
        await player.world.trigger_event(eid)

# ---------------------------------------------------------
# Dialogue execution
# ---------------------------------------------------------

async def run_dialogue(player, npc, node_id):
    """Run a dialogue node."""

    tree = npc.dialogue_tree
    if node_id not in tree:
        await player.send("The NPC seems confused.")
        return

    node = tree[node_id]

    # Check conditions
    if not check_conditions(player, node):
        await player.send(f"{npc.name} refuses to discuss that with you.")
        return

    # Display text
    await player.send(f"\033[94m{npc.name} says:\033[0m \"{node['text']}\"")

    # Apply consequences
    await apply_consequences(player, npc, node)

    # Show choices
    choices = node.get("choices", {})
    if not choices:
        return

    await player.send("Choices:")
    for i, choice in enumerate(choices.keys(), 1):
        await player.send(f" {i}. {choice}")

    # Store dialogue state
    player.dialogue_state = {
        "npc": npc,
        "choices": list(choices.items()),
    }

# ---------------------------------------------------------
# Dialogue choice
# ---------------------------------------------------------

async def do_choose(player, args):
    """Choose a dialogue option."""

    state = getattr(player, "dialogue_state", None)
    if not state:
        await player.send("You are not in a conversation.")
        return

    try:
        idx = int(args) - 1
    except ValueError:
        await player.send("Choose a number.")
        return

    if idx < 0 or idx >= len(state["choices"]):
        await player.send("Invalid choice.")
        return

    _, next_node = state["choices"][idx]
    npc = state["npc"]

    # Continue dialogue
    await run_dialogue(player, npc, next_node)

# ---------------------------------------------------------
# Start dialogue
# ---------------------------------------------------------

async def do_talk(player, args):
    """Talk to an NPC."""

    npc = player.room.find_npc(args)
    if not npc:
        await player.send("They aren't here.")
        return

    if not hasattr(npc, "dialogue_tree"):
        await player.send(f"{npc.name} has nothing to say.")
        return

    await run_dialogue(player, npc, "start")

COMMAND_DEFS = [
    ("talk",   do_talk,   {"position": "standing", "help_category": "dialogue"}),
    ("choose", do_choose, {"position": "standing", "help_category": "dialogue"}),
]
