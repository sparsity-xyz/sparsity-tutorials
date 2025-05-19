import argparse
import asyncio

from util.client import HOST_CID, Client, TCPClient, VSockClient
from util.server import HOST_PROXY_SERVER_PORT, Handler, Server


class LoopbackHandler(Handler):
    # TODO: Implement LoopbackHandler
    pass


class HTTPSServer(Server):
    def __init__(self, handler: Handler):
        super().__init__(443, handler, process_num=2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--vsock", action="store_true",
                        help="Enable vsock mode (optional)")
    args = parser.parse_args()

    if args.vsock:
        cli = VSockClient(HOST_CID, HOST_PROXY_SERVER_PORT)
    else:
        host_addr = "host.docker.internal"
        cli = TCPClient(host_addr, HOST_PROXY_SERVER_PORT)

    https_server = HTTPSServer(LoopbackHandler(cli))
    https_server.start()
