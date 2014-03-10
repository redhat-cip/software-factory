#!/bin/bash

git clone http://sf-gerrit/r/config /root/config
jenkins-jobs update /root/config/jobs
EXIT_CODE=$?
rm -Rf /root/config
