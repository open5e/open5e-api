#!/bin/bash

openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout selfsigned.key -out selfsigned.crt -subj "/C=UA/ST=KS/L=OP/O=Open5e/OU=Awesome/CN=$SERVER_NAME"