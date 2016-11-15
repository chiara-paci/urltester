#!/bin/bash

ca_name=CA
client=dummy_client

if [ ! -f "${ca_name}.key" ]
then
    openssl genrsa -out ${ca_name}.key 4096
fi

if [ ! -f "${ca_name}.crt" ]
then
    openssl req -new -x509 -days 36500 -key ${ca_name}.key -out ${ca_name}.crt
fi

if [ ! -f "${client}.key" ]
then
    openssl genrsa -out ${client}.key 4096
fi

if [ ! -f "${client}.csr" ]
then
    openssl req -new -key ${client}.key -out ${client}.csr
fi

if [ ! -f "${client}.crt" ]
then
    openssl x509 -req -days 36500 -in ${client}.csr -CA ${ca_name}.crt -CAkey ${ca_name}.key -set_serial 01 -out ${client}.crt
fi

if [ ! -f "${client}.p12" ]
then
    openssl pkcs12 -export -clcerts -in ${client}.crt -inkey ${client}.key -out ${client}.p12
fi

if [ ! -f "${client}.pem" ]
then
    openssl pkcs12 -in ${client}.p12 -out ${client}.pem -clcerts
fi
