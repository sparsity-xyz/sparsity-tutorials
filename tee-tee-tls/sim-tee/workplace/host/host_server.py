import asyncio

from util.client import Client
from util.server import Handler


class HostConnectionHandler(Handler):
    client_generator: Client

    def __init__(self, client_generator: Client):
        self.client_generator = client_generator

    async def handle_connection(self, reader, writer):
        client_reader, client_writer = await self.client_generator.async_connect()
        await asyncio.gather(
            self.pipe(reader, client_writer),
            self.pipe(client_reader, writer)
        )
