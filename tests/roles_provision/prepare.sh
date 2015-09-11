#!/bin/bash

. ../../role_configrc

echo "Archive software factory local GIT copy"
(cd ../../; tar -czf /tmp/software-factory-lc.tgz *)
echo "Create softwarefactory archive for version $SF_VER to ${INST}/softwarefactory-${SF_VER}.edeploy"
(cd ${INST}/softwarefactory; tar -c -p --use-compress-program=pigz -f ../softwarefactory-${SF_VER}.edeploy .)
