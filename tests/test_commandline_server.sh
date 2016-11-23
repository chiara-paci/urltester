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


$ut_server --server --base_context="/ciao/gyt" --action="start"

pid=$!
sleep 2
echo "Before: $pid (port: default 9876)"
ps -elf | grep $pid
if ! netstat -an | grep "127.0.0.1:9876"
then
    assert_msg "port default"
    kill  $pid
    exit 2
fi

kill  $pid

echo "After: $pid"
ps -elf | grep $pid

http_port=12345
$ut_server --demo --http_port=$http_port &

pid=$!
sleep 2
echo "Before: $pid (port: $http_port)"
ps -elf | grep $pid

if ! netstat -an | grep 127.0.0.1:$http_port
then
    assert_msg "port 127.0.0.1:$http_port"
    kill  $pid
    exit 2
fi

kill  $pid

echo "After: $pid"
ps -elf | grep $pid


http_port=12345
http_host=0.0.0.0

$ut_server --demo --http_port=$http_port --http_host=$http_host &

pid=$!
sleep 2
echo "Before: $pid (port: $http_port)"
ps -elf | grep $pid

if ! netstat -an | grep $http_host:$http_port
then
    assert_msg "port $http_host:$http_port"
    kill  $pid
    exit 2
fi

kill  $pid

echo "After: $pid"
ps -elf | grep $pid

echo "-------------------------------"
echo
echo "Command line: All tests ok"
echo
