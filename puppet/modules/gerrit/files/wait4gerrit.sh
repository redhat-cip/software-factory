#!/bin/bash

# Wait until port 8080 and 29418 are opened
while [ -z "`netstat -lptn | grep 29418`" ]; do
    sleep 1
    echo -n '.'
done
while [ -z "`netstat -lptn | grep 8080`" ]; do
    sleep 1
    echo -n '.'
done
touch /tmp/wait4gerrit.done
echo
