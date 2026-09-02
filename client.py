"""
Realms of Cyrisea - Simple MUD Client

A deliberately simple TCP terminal client.

Design goals:
- One line of user input = one line sent to the server.
- No automatic blank lines.
- No extra Enter presses.
- Server output is displayed exactly as received.
- Compatible with the asyncio MUD server.
"""

import asyncio
import sys


HOST = "127.0.0.1"
PORT = 4000


# =========================================================
# SERVER READER
# =========================================================

async def receive_from_server(reader):
    """
    Continuously read lines from the MUD server
    and display them exactly as received.
    """

    try:
        while True:

            data = await reader.readline()

            if not data:
                print("\n[Disconnected from server.]")
                return False

            text = data.decode(
                "utf-8",
                errors="replace",
            )

            # The server already supplies line endings.
            # Do NOT add another newline here.
            sys.stdout.write(text)
            sys.stdout.flush()

    except asyncio.CancelledError:
        return False

    except ConnectionResetError:
        print("\n[Connection lost.]")
        return False

    except Exception as exc:
        print(
            f"\n[Receive error: {exc}]"
        )
        return False


# =========================================================
# USER INPUT
# =========================================================

async def send_user_input(writer):
    """
    Read one line from the keyboard and send exactly
    one line to the server.

    The important part is that an empty line is NOT
    generated automatically by the client.
    """

    loop = asyncio.get_running_loop()

    while True:

        try:
            # Run blocking console input in a worker thread
            # so the asyncio server connection remains responsive.
            line = await loop.run_in_executor(
                None,
                sys.stdin.readline,
            )

        except (EOFError, KeyboardInterrupt):
            return False

        if line == "":
            return False

        # Remove ONLY the local Enter/newline.
        #
        # Do not strip the entire string. This means the
        # client does not silently alter what the player typed.
        line = line.rstrip("\r\n")

        # Send exactly one command line.
        payload = (
            line + "\n"
        ).encode("utf-8")

        try:
            writer.write(payload)
            await writer.drain()

        except (ConnectionResetError, BrokenPipeError):
            print(
                "\n[Connection lost.]"
            )
            return False

        except Exception as exc:
            print(
                f"\n[Send error: {exc}]"
            )
            return False


# =========================================================
# MAIN CLIENT
# =========================================================

async def main():

    print(
        f"Connecting to Realms of Cyrisea "
        f"at {HOST}:{PORT}..."
    )

    try:

        reader, writer = await asyncio.open_connection(
            HOST,
            PORT,
        )

    except ConnectionRefusedError:

        print()
        print(
            "Could not connect to the MUD server."
        )
        print(
            f"Make sure the server is running on "
            f"{HOST}:{PORT}."
        )

        return

    except Exception as exc:

        print()
        print(
            f"Connection failed: {exc}"
        )

        return

    print(
        "Connected."
    )
    print()

    # Start receiving server output.
    receiver = asyncio.create_task(
        receive_from_server(reader)
    )

    # Start reading keyboard input.
    sender = asyncio.create_task(
        send_user_input(writer)
    )

    done, pending = await asyncio.wait(
        [receiver, sender],
        return_when=asyncio.FIRST_COMPLETED,
    )

    # Cancel whichever side is still running.
    for task in pending:
        task.cancel()

    if pending:
        await asyncio.gather(
            *pending,
            return_exceptions=True,
        )

    try:
        writer.close()
        await writer.wait_closed()

    except Exception:
        pass

    print()
    print(
        "[Client closed.]"
    )


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":

    try:
        asyncio.run(main())

    except KeyboardInterrupt:

        print()
        print(
            "[Client stopped.]"
        )