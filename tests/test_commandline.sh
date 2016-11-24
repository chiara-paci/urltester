#!/bin/bash

BASE_DIR=$( dirname $0 )
PARENT_DIR=$BASE_DIR/..
BIN_DIR=$PARENT_DIR/bin

function assert_msg {
    local tname="$1"
    echo "$tname failed"
    exit 2
}

ut_server=$BIN_DIR/urltester

if $ut_server --ciao 
then
    assert_msg "ciao (no)"
fi

$ut_server --help    || assert_msg "help"
$ut_server -h        || assert_msg "help (h)"
$ut_server --version || assert_msg "version"
$ut_server -v        || assert_msg "version (v)"

for opt in http_host title template_dir proxy_host
do
    $ut_server --$opt="pippo" || assert_msg "$opt"
done

for opt in http_port proxy_port
do
    $ut_server --$opt=3456 || assert_msg "$opt"
    if $ut_server --$opt="ciao"
    then
	assert_msg "$opt (no)"
    fi
done

$ut_server --config a --config pippo --config pluto || assert_msg config

$ut_server --show_config || assert_msg "show config"
$ut_server --show_config --proxy_host="pippo" || assert_msg "show config"

$ut_server --demo --action start

pid=$!
sleep 2
echo "Before: $pid (port: default 9876)"
ps -elf | grep $pid
if ! netstat -an | grep "127.0.0.1:9876"
then
    assert_msg "port default"
    $ut_server --demo --action stop
    exit 2
fi

$ut_server --demo --action stop

http_port=12345
$ut_server --demo --http_port=$http_port --action start 

pid=$!
sleep 2
echo "Before: $pid (port: $http_port)"

if ! netstat -an | grep 127.0.0.1:$http_port
then
    assert_msg "port 127.0.0.1:$http_port"
    $ut_server --demo --action stop
    exit 2
fi

$ut_server --demo --action stop

echo "After: $pid"
ps -elf | grep $pid


http_port=12345
http_host=0.0.0.0

$ut_server --demo --http_port=$http_port --http_host=$http_host --action start 

pid=$!
sleep 2
echo "Before: $pid (port: $http_port)"
ps -elf | grep $pid

if ! netstat -an | grep $http_host:$http_port
then
    assert_msg "port $http_host:$http_port"
    $ut_server --demo --action stop
    exit 2
fi

$ut_server --demo --action stop

echo "After: $pid"
ps -elf | grep $pid

echo "-------------------------------"
echo
echo "Command line: All tests ok"
echo
