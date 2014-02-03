#!/bin/sh
ssh -o StrictHostKeyChecking=no -i /home/gerrit/ssh_host_rsa_key "$@"
