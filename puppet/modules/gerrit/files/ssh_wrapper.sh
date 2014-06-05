#!/bin/sh
ssh -o StrictHostKeyChecking=no -i /home/gerrit/site_path/etc/ssh_host_rsa_key "$@"
