import argparse
import multiprocessing
import os
import signal
from multiprocessing import Process

import uvicorn
from app import APP
from loopback_server import HTTPSServer, LoopbackHandler
from util.client import HOST_CID, TCPClient, VSockClient
from util.log import logger
from util.server import ENCLAVE_SERVER_PORT, HOST_PROXY_SERVER_PORT, Server


def run_app(vsock):
    app = APP(vsock)

    s = Server(ENCLAVE_SERVER_PORT, vsock=vsock)
    fd = s.fileno()
    uvicorn.run(app.app, fd=fd)


def run_loopback_server(vsock):
    if vsock:
        cli = VSockClient(HOST_CID, HOST_PROXY_SERVER_PORT)
    else:
        host_addr = "host.docker.internal"
        cli = TCPClient(host_addr, HOST_PROXY_SERVER_PORT)

    https_server = HTTPSServer(LoopbackHandler(cli))
    https_server.start()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vsock", action="store_true",
                        help="Enable vsock mode (optional)")
    args = parser.parse_args()

    p1 = Process(target=run_app, args=(args.vsock,))
    p2 = Process(target=run_loopback_server, args=(args.vsock,))

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
