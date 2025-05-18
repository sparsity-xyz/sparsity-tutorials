import os
import abc
import socket
import asyncio


class Client(abc.ABC):
    @abc.abstractmethod
    def connect(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def async_connect(self):
        raise NotImplementedError()


class VSockClient(Client):
    cid: int
    port: int

    def __init__(self, cid: int, port: int):
        self.cid = cid
        self.port = port

    def connect(self):
        host_conn = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
        host_conn.connect((self.cid, self.port))
        return host_conn

    async def async_connect(self):
        loop = asyncio.get_running_loop()
        sock = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
        sock.setblocking(False)

        try:
            sock.connect((self.cid, self.port))
        except BlockingIOError:
            pass

        future = loop.create_future()

        def on_connected():
            if not future.done():
                future.set_result(None)

        loop.add_writer(sock.fileno(), on_connected)

        try:
            await future
        finally:
            loop.remove_writer(sock.fileno())

        err = sock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
        if err != 0:
            raise OSError(err, os.strerror(err))

        return await asyncio.open_connection(sock=sock)


HOST_CID = 2 # socket.VMADDR_CID_HOST


class EnclaveClient(VSockClient):
    def __init__(self, port):
        super().__init__(HOST_CID, port)


class TCPClient(Client):
    host: str
    port: int

    def __init__(self, host, port):
        self.host = host
        self.port = port

    def connect(self):
        host_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host_conn.connect((self.host, self.port))
        return host_conn

    async def async_connect(self):
        loop = asyncio.get_running_loop()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(False)
        await loop.sock_connect(sock, (self.host, self.port))
        # reader / writer
        return await asyncio.open_connection(sock=sock)
