"""
Realms of Cyrisea - Engine Bootstrap
Starts the world, loads modules, launches the server.
"""

import asyncio
import logging

from core import create_default_world, Player
from server import MudServer
from parser import CommandParser

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def main():
    # Create world
    world = create_default_world()
    log.info("World created.")

    # Load command modules
    parser = CommandParser(world)
    parser.load_all_commands()
    log.info("Commands loaded.")

    # Start server
    server = MudServer(world, parser)
    await server.start()

    # Main loop
    while True:
        await asyncio.sleep(0.1)
        await server.process_connections()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server shutting down.")
