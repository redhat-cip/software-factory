#!/bin/bash

# Wait until port 8000 and 29418 are opened
while [ -z "`netstat -lptn | grep 29418`" ]; do
    sleep 1
    echo -n '.'
done
while [ -z "`netstat -lptn | grep 8000`" ]; do
    sleep 1
    echo -n '.'
done
echo
