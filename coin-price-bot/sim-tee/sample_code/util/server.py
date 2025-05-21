import os
import asyncio
import socket
import signal
import multiprocessing
from multiprocessing import Process
from multiprocessing.reduction import send_handle, recv_handle
import pickle
import errno

from util.log import logger


HOST_SERVER_PORT = 8000
HOST_PROXY_SERVER_PORT = 9981
ENCLAVE_SERVER_PORT = 9982


def worker(pipe, family, handler):
    fd = recv_handle(pipe)
    sock = socket.fromfd(fd, family, socket.SOCK_STREAM)
    sock.setblocking(False)
    asyncio.run(start_server(pickle.loads(handler), sock))


async def start_server(handler, sock: socket.socket):
    server = await asyncio.start_server(handler.handle_connection, sock=sock)
    async with server:
        await server.serve_forever()


class Handler:
    async def handle_connection(self, reader, writer):
        raise NotImplementedError()

    @staticmethod
    async def pipe(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            while True:
                data = await reader.read(4096)
                if not data:
                    break
                writer.write(data)
                await writer.drain()
        except (asyncio.CancelledError, ConnectionResetError):
            pass
        except OSError as e:
            if e.errno in (errno.ENOTCONN, errno.ECONNRESET, errno.EPIPE):
                # 107 (Transport endpoint is not connected)
                # 104 (Connection reset by peer)
                # 32  (Broken pipe)
                pass
            else:
                raise
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass


class Server:
    server_port: int
    server: socket.socket
    process_num: int
    processes: list
    running = True

    def __init__(self, server_port: int, conn_handler: Handler=None, process_num: int = 1, vsock=False):
        self.server_port = server_port
        self.vsock = vsock
        if self.vsock:
            self.family = socket.AF_VSOCK
            host_cid = socket.VMADDR_CID_ANY
            self.process_num = 1
        else:
            self.family = socket.AF_INET
            host_cid = "0.0.0.0"
            self.process_num = process_num

        self.server = socket.socket(self.family, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if self.vsock is False:
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

        self.server.bind((host_cid, server_port))
        self.server.listen()
        self.server.setblocking(False)

        self.processes = []
        if conn_handler is None:
            self.handler = Handler()
        else:
            self.handler = conn_handler

        self.parent_conn, self.child_conn = multiprocessing.Pipe()

    def start(self):
        logger.info(f"server listening on host=127.0.0.1, port={self.server_port}, mode: {'vsock' if self.vsock else 'tcp'}, num: {self.process_num}")
        os.setpgid(0, 0)
        signal.signal(signal.SIGINT, lambda s, f: self.shutdown())
        signal.signal(signal.SIGTERM, lambda s, f: self.shutdown())
        self.start_workers()
        self.monitor_workers()

    def fileno(self):
        return self.server.fileno()

    def start_workers(self):
        for _ in range(self.process_num):
            self.start_one_worker()

    def start_one_worker(self):
        p = Process(target=worker, args=(self.child_conn, self.family, pickle.dumps(self.handler), ))
        p.start()
        logger.info(f"worker {p.pid} started.")
        self.processes.append(p)
        send_handle(self.parent_conn, self.server.fileno(), p.pid)

    def monitor_workers(self):
        try:
            while self.running:
                for i, p in enumerate(self.processes):
                    p.join(timeout=0.1)
                    if not p.is_alive() and self.running:
                        logger.info(f"worker {p.pid} died. Restarting...")
                        self.processes.pop(i)
                        self.start_one_worker()
        except KeyboardInterrupt:
            logger.info(f"received Ctrl+C, shutting down...")
            self.shutdown()

    def shutdown(self):
        self.running = False
        for p in self.processes:
            logger.info(f"worker {p.pid} Terminating")
            p.terminate()
        for p in self.processes:
            p.join()
        logger.info(f"worker {len(self.processes)} terminated.")


if __name__ == "__main__":
    s = Server(8000)
    s.start()
