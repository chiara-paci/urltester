#!/bin/bash

BASE_DIR=$( dirname $0 )
PARENT_DIR=$BASE_DIR/..
BIN_DIR=$PARENT_DIR/bin

function assert_msg {
    local tname="$1"
    echo "$tname failed"
    exit 2
}

ut_server=$BIN_DIR/urltester_server.py

if $ut_server --ciao 
then
    assert_msg "ciao (no)"
fi

$ut_server --help    || assert_msg "help"
$ut_server -h        || assert_msg "help (h)"
$ut_server --version || assert_msg "version"
$ut_server -v        || assert_msg "version (v)"

for opt in http_host title template_dir proxy_host proxy_user proxy_password
do
    $ut_server --test --$opt="pippo" || assert_msg "$opt"
done

for opt in http_port proxy_port
do
    $ut_server --test --$opt=3456 || assert_msg "$opt"
    if $ut_server --test --$opt="ciao"
    then
	assert_msg "$opt (no)"
    fi
done

