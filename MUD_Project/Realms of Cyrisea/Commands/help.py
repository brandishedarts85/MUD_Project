"""
Realms of Cyrisea - Unified Help System
Features:
- Auto-generated help from command metadata
- Categories
- Search
- File-based help (help/<topic>.txt)
- Fuzzy matching
- Color formatting
"""

import os
import logging

C_TITLE = "\033[94m"   # blue
C_CMD   = "\033[96m"   # cyan
C_CAT   = "\033[92m"   # green
C_TEXT  = "\033[37m"   # white
C_ERR   = "\033[91m"   # red

HELP_DIR = "help"

log = logging.getLogger(__name__)


async def do_help(player, args):
    """Main help command."""

    from commands import COMMANDS

    # -----------------------------------------------------
    # No argument → show categories AND index.txt
    # -----------------------------------------------------
    if not args:
        # Show command categories
        await player.send(f"{C_TITLE}Help Categories:\033[0m")

        categories = {}
        for name, cmd in COMMANDS.items():
            cat = cmd.help_category or "general"
            categories.setdefault(cat, []).append(name)

        for cat in sorted(categories.keys()):
            await player.send(f"{C_CAT}{cat.capitalize()}\033[0m")

        await player.send("Type 'help <category>' or 'help <command>'.")

        # Show file-based index if it exists
        index_path = os.path.join(HELP_DIR, "index.txt")
        if os.path.exists(index_path):
            await player.send("")
            await send_help_file(player, "index")

        return

    arg = args.lower()

    # -----------------------------------------------------
    # 1. File-based help (exact match)
    # -----------------------------------------------------
    if help_file_exists(arg):
        await send_help_file(player, arg)
        return

    # -----------------------------------------------------
    # 2. File-based help (fuzzy match)
    # -----------------------------------------------------
    match = fuzzy_help_file(arg)
    if match:
        await send_help_file(player, match)
        return

    # -----------------------------------------------------
    # 3. Category lookup
    # -----------------------------------------------------
    categories = {}
    for name, cmd in COMMANDS.items():
        cat = cmd.help_category or "general"
        categories.setdefault(cat, []).append(name)

    if arg in categories:
        await player.send(f"{C_TITLE}{arg.capitalize()} Commands:\033[0m")
        for name in sorted(categories[arg]):
            await player.send(f"  {C_CMD}{name}\033[0m")
        return

    # -----------------------------------------------------
    # 4. Command lookup (prefix)
    # -----------------------------------------------------
    for name, cmd in COMMANDS.items():
        if name.startswith(arg):
            await show_command_help(player, name, cmd)
            return

    # -----------------------------------------------------
    # 5. Nothing found
    # -----------------------------------------------------
    await player.send(f"{C_ERR}No help found for '{arg}'.\033[0m")


# ---------------------------------------------------------
# File-based help utilities
# ---------------------------------------------------------

def help_file_exists(topic):
    return os.path.exists(os.path.join(HELP_DIR, f"{topic}.txt"))

def fuzzy_help_file(topic):
    try:
        for filename in os.listdir(HELP_DIR):
            if filename.endswith(".txt"):
                name = filename[:-4]
                if name.startswith(topic):
                    return name
    except FileNotFoundError:
        log.error("Help directory missing.")
    return None

async def send_help_file(player, topic):
    path = os.path.join(HELP_DIR, f"{topic}.txt")

    if not os.path.exists(path):
        await player.send(f"{C_ERR}Help file missing: {topic}\033[0m")
        return

    await player.send(f"{C_TITLE}--- {topic.upper()} ---\033[0m")

    try:
        with open(path, "r") as f:
            for line in f:
                await player.send(f"{C_TEXT}{line.rstrip()}\033[0m")
    except Exception as e:
        log.error(f"Error reading help file {topic}: {e}")
        await player.send(f"{C_ERR}Error loading help file.\033[0m")


# ---------------------------------------------------------
# Command help (your original system)
# ---------------------------------------------------------

async def show_command_help(player, name, cmd):
    await player.send(f"{C_TITLE}Help: {name}\033[0m")

    cat = cmd.help_category or "general"
    await player.send(f"{C_CAT}Category:\033[0m {cat}")

    if cmd.admin > 0:
        await player.send(f"{C_CAT}Admin Level:\033[0m {cmd.admin}")

    await player.send(f"{C_CAT}Required Position:\033[0m {cmd.position}")

    desc = cmd.func.__doc__ or "No description available."
    await player.send(f"{C_TEXT}{desc.strip()}\033[0m")


# ---------------------------------------------------------
# Command definition
# ---------------------------------------------------------

COMMAND_DEFS = [
    ("help", do_help, {"position": "resting", "help_category": "general"}),
]
