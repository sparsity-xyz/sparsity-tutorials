#!/bin/bash

  LOG=/tmp/tee.log

if [ "$LOCAL" = "true" ]; then
    echo "MODE: Local"

    echo "nameserver 127.0.0.1" > /etc/resolv.conf

    dnsmasq

    echo "start app"
    python /app/main.py
else
    echo "MODE: TEE"

    ip addr add 127.0.0.1/32 dev lo
    ip link set dev lo up

    echo "nameserver 127.0.0.1" > /tmp/resolv.conf

    dnsmasq --resolv-file=/tmp/resolv.conf

    echo "start app"
    python /app/main.py --vsock
fi
