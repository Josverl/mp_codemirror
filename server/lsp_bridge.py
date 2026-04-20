#!/usr/bin/env python3
"""
WebSocket Bridge for Pyright LSP Server

This server acts as a bridge between the browser (WebSocket client)
and the Pyright LSP server (stdio).

Architecture:
    Browser <--WebSocket--> Bridge <--stdio--> Pyright
"""

import asyncio
import json
import logging
import subprocess
from pathlib import Path

import websockets

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PyrightBridge:
    """Bridge between WebSocket client and Pyright LSP server"""

    def __init__(self):
        self.pyright_process = None
        self.client_websocket = None

    async def start_pyright(self):
        """Start Pyright LSP server as subprocess"""
        logger.info("Starting Pyright LSP server...")

        try:
            self.pyright_process = await asyncio.create_subprocess_exec(
                "pyright-langserver",
                "--stdio",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            logger.info("Pyright LSP server started successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to start Pyright: {e}")
            return False

    async def stop_pyright(self):
        """Stop Pyright LSP server"""
        if self.pyright_process:
            logger.info("Stopping Pyright LSP server...")
            self.pyright_process.terminate()
            await self.pyright_process.wait()
            logger.info("Pyright LSP server stopped")

    async def read_from_pyright(self):
        """Read messages from Pyright and forward to WebSocket client"""
        if not self.pyright_process or not self.pyright_process.stdout:
            return

        try:
            while True:
                # Read Content-Length header
                header = await self.pyright_process.stdout.readline()
                if not header:
                    logger.warning("Pyright stdout closed")
                    break

                header = header.decode("utf-8").strip()
                if not header.startswith("Content-Length:"):
                    continue

                # Parse content length
                content_length = int(header.split(":")[1].strip())

                # Read empty line
                await self.pyright_process.stdout.readline()

                # Read message content
                content = await self.pyright_process.stdout.read(content_length)
                message = content.decode("utf-8")

                logger.debug(f"Pyright -> Browser: {message[:100]}...")

                # Forward to WebSocket client
                if self.client_websocket:
                    await self.client_websocket.send(message)

        except Exception as e:
            logger.error(f"Error reading from Pyright: {e}")

    async def write_to_pyright(self, message: str):
        """Write message to Pyright stdin"""
        if not self.pyright_process or not self.pyright_process.stdin:
            logger.error("Pyright process not available")
            return

        try:
            # Format as LSP message with Content-Length header
            content = message.encode("utf-8")
            header = f"Content-Length: {len(content)}\r\n\r\n".encode("utf-8")

            self.pyright_process.stdin.write(header + content)
            await self.pyright_process.stdin.drain()

            logger.debug(f"Browser -> Pyright: {message[:100]}...")

        except Exception as e:
            logger.error(f"Error writing to Pyright: {e}")

    async def handle_client(self, websocket):
        """Handle WebSocket client connection"""
        self.client_websocket = websocket
        client_address = websocket.remote_address
        logger.info(f"Client connected from {client_address}")

        # Start Pyright if not already running
        if not self.pyright_process:
            if not await self.start_pyright():
                await websocket.close(1011, "Failed to start Pyright")
                return

            # Start reading from Pyright
            asyncio.create_task(self.read_from_pyright())

        try:
            # Forward messages from client to Pyright
            async for message in websocket:
                logger.debug(f"Received from client: {message[:100]}...")
                await self.write_to_pyright(message)

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client {client_address} disconnected")
        except Exception as e:
            logger.error(f"Error handling client: {e}")
        finally:
            self.client_websocket = None


async def main():
    """Main entry point"""
    host = "localhost"
    port = 8765

    bridge = PyrightBridge()

    logger.info(f"Starting WebSocket server on ws://{host}:{port}")

    async with websockets.serve(bridge.handle_client, host, port):
        logger.info("WebSocket server running. Press Ctrl+C to stop.")
        try:
            await asyncio.Future()  # Run forever
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            await bridge.stop_pyright()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
