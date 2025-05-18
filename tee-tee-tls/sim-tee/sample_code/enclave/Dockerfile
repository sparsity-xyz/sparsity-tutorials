FROM python:3.9.6-slim

RUN apt-get update && \
    apt-get install -y dnsmasq iproute2 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY apps/coinbot/requirements.txt .
RUN pip install -r requirements.txt

RUN echo "address=/#/127.0.0.1" > /etc/dnsmasq.conf

WORKDIR /app

COPY enclave .
COPY util ./util
COPY entrypoint.sh /entrypoint.sh

# replace app with the agent app
COPY apps/coinbot/* ./

COPY apps/coinbot/Certificate.crt /usr/local/share/ca-certificates/Certificate.crt
RUN update-ca-certificates

# fix windows line endings issue
RUN chmod +x /entrypoint.sh && sed -i 's/\r$//' /entrypoint.sh

CMD ["/entrypoint.sh"]
