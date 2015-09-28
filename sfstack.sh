#!/bin/bash
# Small utility to deploy SF like OpenStack devstack

set -e

echo "[+] Install dependencies"
sudo yum update -y
sudo yum install -y libvirt-daemon-lxc
sudo systemctl restart libvirtd

echo "[+] Fetch image"
./fetch_image.sh

echo "[+] Make sure no instance is already running"
(cd deploy/lxc; sudo ./deploy.py stop)

echo "[+] Start LXC container"
(cd deploy/lxc; sudo ./deploy.py init)

echo "[+] Wait for ssh"
sleep 5
sed -i 's/.*192\.168\.135\.101.*//' ~/.ssh/known_hosts

echo "[+] Auto configure"
ssh root@192.168.135.101 "cd bootstraps; ./bootstrap.sh" > /dev/null

echo "[+] Run serverspec"
ssh root@192.168.135.101 "cd serverspec; rake spec"

echo "[+] SF is ready to be used:"
echo "echo PUBLIC_IP tests.dom | sudo tee -a /etc/hosts"
echo "firefox https://tests.dom"
