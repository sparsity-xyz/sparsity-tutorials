import argparse
import multiprocessing
import os
import signal
from multiprocessing import Process

from host_proxy import HostProxyHandler
from host_server import HostConnectionHandler
from util.client import TCPClient, VSockClient
from util.log import logger
from util.server import (ENCLAVE_SERVER_PORT, HOST_PROXY_SERVER_PORT,
                         HOST_SERVER_PORT, Server)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vsock", action="store_true",
                        help="Enable vsock mode (optional)")
    parser.add_argument("--cid", type=int, default=None,
                        help="Enclave CID (optional)")
    args = parser.parse_args()

    if args.vsock:
        cli = VSockClient(args.cid, ENCLAVE_SERVER_PORT)
    else:
        enclave_addr = "127.0.0.1"
        cli = TCPClient(enclave_addr, ENCLAVE_SERVER_PORT)

    # server must be a TCP server
    server = Server(HOST_SERVER_PORT, HostConnectionHandler(cli), 2)
    proxy = Server(HOST_PROXY_SERVER_PORT, HostProxyHandler(), 2, args.vsock)
    p1 = Process(target=server.start)
    p2 = Process(target=proxy.start)

    p1.start()
    p2.start()

    try:
        p1.join()
        p2.join()
    except KeyboardInterrupt:
        logger.info("caught Ctrl+C, shutting down...")
        try:
            os.killpg(p1.pid, signal.SIGTERM)
        except Exception as e:
            logger.error("failed to kill p1 group, %s", e)
        try:
            os.killpg(p2.pid, signal.SIGTERM)
        except Exception as e:
            logger.error("failed to kill p2 group, %s", e)

        p1.join()
        p2.join()
        logger.info("all servers shutdown cleanly.")


if __name__ == '__main__':
    multiprocessing.set_start_method('spawn')  # for Windows / Mac / Linux
    main()
