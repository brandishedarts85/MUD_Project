"""
Realms of Cyrisea - Socket Server
Handles player connections, input, output.
"""

import asyncio
import logging
from core import Player

# NEW: account + character systems
from accounts import login_flow, character_selection_flow

# NEW: PvP world tick systems
from commands.pvp import process_hostility, process_corpses

log = logging.getLogger(__name__)


class MudServer:
    def __init__(self, world, parser, host="0.0.0.0", port=4000):
        self.world = world
        self.parser = parser
        self.host = host
        self.port = port
        self.server = None
        self.connections = {}  # reader -> Player

    async def start(self):
        self.server = await asyncio.start_server(
            self.handle_connection, self.host, self.port
        )
        log.info(f"Server listening on {self.host}:{self.port}")

        # Start world tick loop
        asyncio.create_task(self.process_connections())

    async def handle_connection(self, reader, writer):
        addr = writer.get_extra_info("peername")
        log.info(f"Connection from {addr}")

        # -----------------------------------------------------
        # LOGIN FLOW
        # -----------------------------------------------------
        account = await login_flow(self, reader, writer)
        if not account:
            writer.write(b"Login failed.\n")
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            return

        # -----------------------------------------------------
        # CHARACTER SELECTION / CREATION
        # -----------------------------------------------------
        player = await character_selection_flow(self, reader, writer, account)
        if not player:
            writer.write(b"Character load/creation failed.\n")
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            return

        # Add player to world
        self.world.players.append(player)
        self.connections[reader] = player

        await player.send("Welcome to Realms of Cyrisea.")
        await player.send("Type 'help' for commands.")

        # If character has no room (new character), place them in default room
        if not player.room and self.world.rooms:
            first_room = next(iter(self.world.rooms.values()))
            await first_room.enter(player)

        # -----------------------------------------------------
        # INPUT LOOP
        # -----------------------------------------------------
        while True:
            try:
                data = await reader.readline()
                if not data:
                    break
                text = data.decode().strip()
                await self.parser.handle_command(player, text)
            except ConnectionResetError:
                break

        # Disconnect
        await self.disconnect(reader, writer)

    async def disconnect(self, reader, writer):
        player = self.connections.get(reader)
        if player:
            if player.room:
                await player.room.leave(player)
            if player in self.world.players:
                self.world.players.remove(player)
            del self.connections[reader]
            log.info(f"{player.name} disconnected.")

        writer.close()
        await writer.wait_closed()

    async def process_connections(self):
        """
        World tick loop:
        - hostility timers
        - corpse decay
        """
        while True:
            await asyncio.sleep(1)

            # Hostility expiration
            await process_hostility(self.world)

            # Corpse decay
            await process_corpses(self.world)
