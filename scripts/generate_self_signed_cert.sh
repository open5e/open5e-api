#!/bin/bash
source .env

echo "KEYFILE = $KEYFILE"
echo "CERTFILE = $CERTFILE"
echo "SERVER_NAME = $SERVER_NAME"

if [ "$CERTFILE" = "selfsigned.crt" ]; then
    echo "Generating Self-signed certs."

    rm selfsigned.*

    openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout $KEYFILE -out $CERTFILE -subj "/C=UA/ST=KS/L=OP/O=Open5e/OU=Awesome/CN=$SERVER_NAME"
fi