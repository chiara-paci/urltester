#!/bin/bash

BASE_DIR=$( dirname $0 )
PARENT_DIR=$BASE_DIR/..
BIN_DIR=$PARENT_DIR/bin

ut_server=$BIN_DIR/urltester

function help {
    echo "$0 -h | -c | -b | -u "
    echo
    echo "-b: basic"
    echo "-c: command line"
    echo "-u: urllib"
}

commandline=""
basic=""
urllib=""

while getopts "Phcbu" opzione
do
    case $opzione in
	h) help;exit;;
	c) commandline="yes";;
	b) basic="yes";;
	u) urllib="yes";;
    esac
done

if [ "$commandline" ]
then
    ./test_commandline.sh
fi

if [ "$basic" ]
then
    echo "==========================================================="
    echo "Basic tests"
    echo "==========================================================="
    echo 
    ./test_basic.py
    echo
fi

if [ "$urllib" ]
then
    echo "==========================================================="
    echo "Urllib tests"
    echo "==========================================================="
    echo 
    echo "Starting test server..."
    echo "................................................"
    $ut_server --server &
    pid=$!
    sleep 2
    
    ./test_urllib.py

    echo "................................................"
    echo "Stopping test server..."
    echo
    kill $pid
    echo
fi
