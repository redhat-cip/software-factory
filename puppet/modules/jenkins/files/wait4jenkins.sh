#!/bin/bash

RETRIES=0
while true; do
    wget --spider http://localhost:8082/jenkins/
    [ $? -eq 0 ] && break
    let RETRIES=RETRIES+1
    [ "$RETRIES" == "90" ] && {
        ps afxww
        echo "Jenkins took too long to be up !"
        exit 1
    }
    sleep 10
done
