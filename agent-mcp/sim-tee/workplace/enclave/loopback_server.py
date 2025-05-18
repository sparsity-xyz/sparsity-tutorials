import argparse
import asyncio

from util.client import Client
from util.client import TCPClient
from util.client import VSockClient, HOST_CID
from util.server import Server, Handler, HOST_PROXY_SERVER_PORT


class LoopbackHandler(Handler):
    client_generator: Client

    def __init__(self, client_generator: Client):
        self.client_generator = client_generator

    async def handle_connection(self, reader, writer):
        client_reader, client_writer = await self.client_generator.async_connect()
        await asyncio.gather(
            self.pipe(reader, client_writer),
            self.pipe(client_reader, writer)
        )


class HTTPSServer(Server):
    def __init__(self, handler: Handler):
        super().__init__(443, handler, process_num=2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--vsock", action="store_true", help="Enable vsock mode (optional)")
    args = parser.parse_args()

    if args.vsock:
        cli = VSockClient(HOST_CID, HOST_PROXY_SERVER_PORT)
    else:
        host_addr = "host.docker.internal"
        cli = TCPClient(host_addr, HOST_PROXY_SERVER_PORT)

    https_server = HTTPSServer(LoopbackHandler(cli))
    https_server.start()
