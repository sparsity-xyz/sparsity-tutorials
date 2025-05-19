FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y dnsmasq iproute2 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip


COPY requirements.txt .
RUN pip install -r requirements.txt

RUN echo "address=/#/127.0.0.1" > /etc/dnsmasq.conf

WORKDIR /app

COPY enclave .
COPY util ./util
COPY entrypoint.sh /entrypoint.sh


# fix windows line endings issue
RUN chmod +x /entrypoint.sh && sed -i 's/\r$//' /entrypoint.sh

CMD ["/entrypoint.sh"]
