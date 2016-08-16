#!/bin/bash
# Default configurations

set -e
[ -z "${DEBUG}" ] || set -x

export PATH=/bin:/sbin:/usr/local/bin:/usr/local/sbin
OS_PASSWORD=${OS_PASSWORD:-sf4ever}

sudo packstack --allinone --os-swift-install=y --os-ceilometer-install=n --nagios-install=n \
    --provision-demo=n --keystone-admin-passwd=${OS_PASSWORD} --os-heat-install=y --cinder-volumes-size=50G

export OS_USERNAME=admin
export OS_PASSWORD
export OS_AUTH_URL=http://localhost:5000/v2.0
export OS_TENANT_NAME=admin
export OS_REGION_NAME=RegionOne

echo "[+] Prepare external network provider"
sudo openstack-config --set /etc/neutron/plugins/ml2/openvswitch_agent.ini ovs bridge_mappings extnet:br-ex
sudo openstack-config --set /etc/neutron/plugin.ini ml2 type_drivers vxlan,flat,vlan
sudo service neutron-openvswitch-agent restart
sudo service neutron-server restart

echo "[+] Allow external access from vm"
gw=$(ip route get 8.8.8.8 | awk '/dev/ { print $5 }')
sudo iptables -I POSTROUTING -t nat -s 192.168.42.1/24 -o $gw -j MASQUERADE
sudo iptables -I FORWARD -i br-ex -o $gw -j ACCEPT
sudo iptables -I FORWARD -o br-ex -i $gw -j ACCEPT

echo "[+] Fix nova compute virt_type"
sudo openstack-config --set /etc/nova/nova.conf libvirt virt_type kvm
sudo openstack-config --set /etc/nova/nova.conf libvirt cpu_mode host-passthrough
sudo systemctl restart openstack-nova-compute

echo "[+] Create network"
neutron net-create external_network --provider:network_type flat --provider:physical_network extnet --router:external > /dev/null
neutron subnet-create --name public_subnet --enable_dhcp=False \
    --allocation-pool=start=192.168.42.10,end=192.168.42.200 \
    --gateway=192.168.42.1 external_network 192.168.42.0/24 > /dev/null
neutron router-create external_gw > /dev/null
neutron router-gateway-set external_gw external_network > /dev/null
sudo ip a add 192.168.42.1/24 dev br-ex

echo "[+] Install cirros"
wget http://download.cirros-cloud.net/0.3.4/cirros-0.3.4-x86_64-disk.img &> /dev/null
glance image-create --name=cirros --visibility=public --container-format=bare --disk-format=qcow2 < cirros-0.3.4-x86_64-disk.img > /dev/null

echo "[+] Create 3 tenants"
(for tenantname in sfmain sfnodepool sfswift; do
    openstack project create $tenantname
    openstack user create --project $tenantname --password ${OS_PASSWORD} $tenantname
    openstack role add --project $tenantname --user $tenantname heat_stack_owner
done) > /dev/null
[ -f ~/.ssh/id_rsa ] || ssh-keygen -N '' -f ~/.ssh/id_rsa

echo "[+] Customize tenants"
(for tenantname in admin sfmain sfnodepool sfswift; do
    export OS_USERNAME=$tenantname
    export OS_TENANT_NAME=$tenantname

    echo "[+] Create network"
    neutron net-create ${tenantname}_network
    neutron subnet-create --name ${tenantname}_subnet --enable_dhcp=True \
        --allocation-pool=start=192.168.201.10,end=192.168.201.200   \
        --gateway 192.168.201.1 ${tenantname}_network 192.168.201.0/24
    neutron router-create ${tenantname}_gw
    neutron router-gateway-set ${tenantname}_gw external_network
    neutron router-interface-add ${tenantname}_gw ${tenantname}_subnet

    echo "[+] Allow ping and ssh"
    neutron security-group-rule-create --direction ingress --protocol ICMP default
    neutron security-group-rule-create --direction ingress --protocol TCP --port-range-min 22 --port-range-max 22 default

    echo "[+] Create Keypairs"
    nova keypair-add --pub-key ~/.ssh/id_rsa.pub id_rsa
done) > /dev/null
