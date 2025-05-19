# Coin Price Bot TEE Tutorial

This tutorial will guide you through implementing the missing logic for a secure, retrieval-augmented agent inside a TEE, using the coin-price-bot framework. You will:
- Implement the missing handler classes and entrypoint logic in `workspace/` by referencing `sample_code/`.
- Enable secure, attested AI chat and retrieval-augmented generation (RAG) via the TEE.

---

## Sidenote: Prerequisites & Tools
- This project assumes you are already familiar with Docker, dnsmasq, and the basic TEE-tls container setup.
- All DNS routing, container networking, and peripheral setup (dnsmasq, entrypoint, etc.) are already handled for you.
- If you need a refresher, see the `sample_code` or previous tutorials in this codebase.

---

## 1. Implement the Missing Pieces in `workspace/`

You must implement the following missing classes and logic in your `workspace/` directory. For each, refer to the corresponding file in `sample_code/` and adapt the code as needed.

### A. LoopbackHandler (`workspace/enclave/loopback_server.py`)
Replace the `#TODO: Implement LoopbackHandler` section with the following logic:
```python
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
```
Reference: `sample_code/enclave/loopback_server.py`

### B. HostProxyHandler (`workspace/host/host_proxy.py`)
Replace the `#TODO: Implement HostProxyHandler` section with the following logic:
```python
class HostProxyHandler(Handler):
    async def handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            msg_peek = await reader.read(1024)
            if not msg_peek:
                logger.warning("Connection closed before data received")
                writer.close()
                await writer.wait_closed()
                return

            sni = self.extract_sni(msg_peek)
            if sni is None:
                logger.warning(f"SNI not found")
                writer.close()
                await writer.wait_closed()
                return

            client_reader, client_writer = await asyncio.open_connection(sni, 443)
            client_writer.write(msg_peek)
            await client_writer.drain()
            await asyncio.gather(
                self.pipe(reader, client_writer),
                self.pipe(client_reader, writer)
            )
        except Exception as e:
            logger.error(f"Handle connection error: {e}")
            writer.close()
            await writer.wait_closed()
```
Reference: `sample_code/host/host_proxy.py`

### C. HostConnectionHandler (`workspace/host/host_server.py`)
Replace the `#TODO: Implement HostConnectionHandler` section with the following logic:
```python
async def handle_connection(self, reader, writer):
    client_reader, client_writer = await self.client_generator.async_connect()
    await asyncio.gather(
        self.pipe(reader, client_writer),
        self.pipe(client_reader, writer)
    )
```
Reference: `sample_code/host/host_server.py`

### D. entrypoint.sh (`workspace/entrypoint.sh`)
Implement the local mode logic as in the sample. For example:
```bash
if [ "$LOCAL" = "true" ]; then
    echo "MODE: Local"
    echo "nameserver 127.0.0.1" > /etc/resolv.conf
    dnsmasq
    echo "start app"
    python /app/main.py
else
    ip addr add 127.0.0.1/32 dev lo
    ip link set dev lo up
    echo "nameserver 127.0.0.1" > /tmp/resolv.conf
    dnsmasq --resolv-file=/tmp/resolv.conf
    echo "start app"
    python /app/main.py --vsock
fi
```
Reference: `sample_code/entrypoint.sh`

---

## 2. How to Run and Test

Follow these steps to run and test your implementation:

1. **Start the host proxy/server:**
   ```bash
   make run-host
   ```
2. **Build and run the coin-price-bot (TEE) container:**
   ```bash
   make build-ag2-mcp && make run-ag2-mcp-local
   ```
3. **Run the client to interact with the setup:**
   - In a new terminal, go to the `client` directory (if provided):
     ```bash
     cd coin-price-bot/sim-tee/client
     ```
   - Set the required environment variables as described in the client README (if provided):
     ```bash
     export PYTHONPATH="$PYTHONPATH:$PWD"
     export PLATFORM_API_KEY=<openai_api_key>
     export PLATFORM=openai
     export MODEL=gpt-4
     export TEE_TLS_URL=http://localhost:8000/
     ```
   - Run the client:
     ```bash
     python3 main.py
     ```

See the client README for more details on the environment variables and client usage.

---

## 3. Reference
- For API and class details, see the `sample_code` and the coin-price-bot framework documentation.
- For peripheral setup (dnsmasq, Docker, etc.), refer to previous tutorials or the provided Makefile and Dockerfile.

---

**Your goal:** Implement the missing logic in `workspace/` as described above. All other infrastructure is already in place. Good luck! 