import asyncio

from util.client import Client
from util.server import Handler


class HostConnectionHandler(Handler):
    client_generator: Client

    def __init__(self, client_generator: Client):
        self.client_generator = client_generator

    async def handle_connection(self, reader, writer):
        # TODO: Implement HostConnectionHandler
        pass
