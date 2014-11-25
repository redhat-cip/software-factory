#!/bin/bash

. ../../role_configrc

orig=$(pwd)
echo "Archive software factory local GIT copy"
tar -czf /tmp/software-factory-lc.tgz ../..
cd ${INST}/install-server-vm
echo "Create install-server-vm archive for version $SF_VER"
tar -c --use-compress-program=pigz -f ../install-server-vm-${SF_VER}.edeploy .
cd ${INST}/softwarefactory
echo "Create softwarefactory archive for version $SF_VER"
tar -c --use-compress-program=pigz -f ../softwarefactory-${SF_VER}.edeploy .
cd $orig
