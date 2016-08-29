#!/bin/sh
ssh -o StrictHostKeyChecking=no -i /root/gerrit_admin_rsa "$@"
