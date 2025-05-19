import asyncio
from typing import Optional

from util.log import logger
from util.server import Handler


class HostProxyHandler(Handler):
    async def handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        # TODO: Implement HostProxyHandler
        pass

    @staticmethod
    def extract_sni(data: bytes) -> Optional[str]:
        try:
            if len(data) < 5 or data[0] != 0x16:
                raise ValueError("Not a TLS handshake record")

            # Skip record header
            idx = 5

            # Check handshake type
            if data[idx] != 0x01:
                raise ValueError("Not a ClientHello")

            # Skip handshake header (1 + 3 bytes length)
            idx += 4

            # Skip client_version, random
            idx += 2 + 32

            # Session ID
            session_id_len = data[idx]
            idx += 1 + session_id_len

            # Cipher suites
            cipher_suites_len = int.from_bytes(data[idx:idx + 2], 'big')
            idx += 2 + cipher_suites_len

            # Compression methods
            comp_methods_len = data[idx]
            idx += 1 + comp_methods_len

            # Extensions total length
            ext_total_len = int.from_bytes(data[idx:idx + 2], 'big')
            idx += 2

            end = idx + ext_total_len
            while idx + 4 <= end:
                ext_type = int.from_bytes(data[idx:idx + 2], 'big')
                ext_len = int.from_bytes(data[idx + 2:idx + 4], 'big')
                ext_data = data[idx + 4:idx + 4 + ext_len]

                if ext_type == 0x00:  # SNI
                    # ext_data: [list_len(2)][type(1)=0][name_len(2)][name]
                    list_len = int.from_bytes(ext_data[0:2], 'big')
                    if ext_data[2] != 0:  # name type != host_name
                        break
                    name_len = int.from_bytes(ext_data[3:5], 'big')
                    server_name = ext_data[5:5 + name_len].decode()
                    return server_name

                idx += 4 + ext_len

        except Exception as e:
            logger.error(f"Failed to extract sni: {e}")

        return None
