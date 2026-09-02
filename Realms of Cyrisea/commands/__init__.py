"""
Realms of Cyrisea - Command System
Defines:
- Command metadata object
- Global command table
- Registration utilities
"""

import logging

# Import command modules
from .movement import *
from .info import *
from .comm import *
from .admin import *
from .combat import *
from .magic import *
from .socials import *


class Command:
    """
    Metadata-rich command object.
    Mirrors SMAUG's cmd_type structure but modernized.
    """

    def __init__(self, func, position="standing", admin=0, log=False, help_category="general"):
        self.func = func              # async function(player, args)
        self.position = position      # standing, resting, fighting, dead
        self.admin = admin            # admin level required
        self.log = log                # log command usage
        self.help_category = help_category


COMMANDS = {}


def register(name, func, **kwargs):
    """
    Register a command in the global table.
    Example:
        register("look", do_look, position="resting")
    """
    name = name.lower()

    if name in COMMANDS:
        logging.warning(f"Duplicate command registration: {name}")

    COMMANDS[name] = Command(func, **kwargs)


def load_commands():
    """
    Load all commands from modules.
    Each module exposes a 'COMMAND_DEFS' list of tuples:
        ("command_name", function, metadata)
    """

    from .movement import COMMAND_DEFS as MOVE_CMDS
    from .info import COMMAND_DEFS as INFO_CMDS
    from .comm import COMMAND_DEFS as COMM_CMDS
    from .admin import COMMAND_DEFS as ADMIN_CMDS
    from .combat import COMMAND_DEFS as COMBAT_CMDS
    from .magic import COMMAND_DEFS as MAGIC_CMDS
    from .socials import COMMAND_DEFS as SOCIAL_CMDS

    all_defs = (
        MOVE_CMDS +
        INFO_CMDS +
        COMM_CMDS +
        ADMIN_CMDS +
        COMBAT_CMDS +
        MAGIC_CMDS +
        SOCIAL_CMDS
    )

    for name, func, meta in all_defs:
        register(name, func, **meta)

    logging.info(f"{len(COMMANDS)} commands loaded.")


# Load commands immediately when module is imported
load_commands()
