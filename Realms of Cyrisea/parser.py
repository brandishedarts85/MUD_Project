"""
Realms of Cyrisea - Command Parser
Loads command modules, dispatches commands.
"""

import logging
import importlib
import pkgutil

log = logging.getLogger(__name__)


class CommandParser:
    def __init__(self, world):
        self.world = world
        self.commands = {}  # name -> function

    def load_all_commands(self):
        import commands

        for module_info in pkgutil.iter_modules(commands.__path__):
            module_name = module_info.name
            module = importlib.import_module(f"commands.{module_name}")

            if hasattr(module, "COMMAND_DEFS"):
                for name, func, meta in module.COMMAND_DEFS:
                    self.commands[name] = func
                    log.info(f"Loaded command: {name} from {module_name}")

    async def handle_command(self, player, text):
        if not text:
            return

        parts = text.split(" ", 1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if cmd in self.commands:
            try:
                await self.commands[cmd](player, args)
            except Exception as e:
                log.exception("Command error")
                await player.send("An error occurred.")
        else:
            await player.send("Unknown command.")
