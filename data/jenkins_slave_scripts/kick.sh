#!/bin/bash

git clone http://sf-gerrit/r/config /root/config
jenkins-jobs update /tmp/config
EXIT_CODE=$?
rm -Rf /root/config
