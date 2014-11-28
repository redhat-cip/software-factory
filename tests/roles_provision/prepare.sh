#!/bin/bash

. ../../role_configrc

echo "Archive software factory local GIT copy"
(cd ../../; tar -czf /tmp/software-factory-lc.tgz *)
echo "Create install-server-vm archive for version $SF_VER to ${INST}/install-server-vm-${SF_VER}.edeploy"
(cd ${INST}/install-server-vm; tar -c -p --use-compress-program=pigz -f ../install-server-vm-${SF_VER}.edeploy .)
echo "Create softwarefactory archive for version $SF_VER to ${INST}/softwarefactory-${SF_VER}.edeploy"
(cd ${INST}/softwarefactory; tar -c -p --use-compress-program=pigz -f ../softwarefactory-${SF_VER}.edeploy .)
