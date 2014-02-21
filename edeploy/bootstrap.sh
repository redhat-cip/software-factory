#!/bin/bash

. ../function.sh

TIMESTAMP=`date +"%Y%m%d"`
PREFIX="edeploy-$TIMESTAMP-"
VM_FLAVOR="10"
ROLES="puppetmaster mysql ldap redmine jenkins gerrit "
RELEASE="D7-H.1.0.0"
SUMMARY=""

SECURITY_GROUP="${PREFIX}sg"
nova secgroup-create $SECURITY_GROUP "Software Factory"
***REMOVED***
nova secgroup-add-rule $SECURITY_GROUP tcp 22 22 94.143.116.0/24  # VPN
nova secgroup-add-rule $SECURITY_GROUP tcp 22 22 46.231.128.0/24
***REMOVED***
nova secgroup-add-rule $SECURITY_GROUP tcp 29418 29418 94.143.116.0/24  # VPN
nova secgroup-add-rule $SECURITY_GROUP tcp 29418 29418 46.231.128.0/24
nova secgroup-add-rule $SECURITY_GROUP tcp 80 80 0.0.0.0/0
nova secgroup-add-rule $SECURITY_GROUP tcp 8080 8080 0.0.0.0/0

# This make sure ${BUILD} is clean
new_build

# VM boot
for ROLENAME in $ROLES; do
    VM_NAME="$PREFIX$ROLENAME"

    echo "Processing $VM_NAME"

    if [ "$1" == "recreate" ]; then
        rm /var/lib/debootstrap/install/D7-H.1.0.0/$ROLENAME-D7-H.1.0.0.img*
        rm /var/lib/debootstrap/install/D7-H.1.0.0/$ROLENAME.done
    fi

    if [ ! -e "/var/lib/debootstrap/install/D7-H.1.0.0/$ROLENAME-D7-H.1.0.0.img.qcow2" ]; then
        make $ROLENAME
    fi

    IMAGE_ID=`glance image-list | grep $PREFIX$ROLENAME  | cut -f 2 -d " "`

    if [ "$IMAGE_ID" == "" ]; then
        echo "Registering image in Glance..."

        GLANCE_OUTPUT=`glance -v image-create --name="$VM_NAME" --container-format ovf --disk-format qcow2 < /var/lib/debootstrap/install/$RELEASE/$ROLENAME-$RELEASE.img.qcow2`

        # Get image ID
        IMAGE_ID=`echo  $GLANCE_OUTPUT | grep -ohe "id | [0-9a-f-]\{36\}" | cut -c 6-`
    fi

    echo "Booting new VM..."

    if [ "$ROLENAME" == "puppetmaster" ]; then
        # puppetmaster cloudinit file can be used directly
        cp ../cloudinit/puppetmaster.cloudinit ${BUILD}/cloudinit/puppetmaster.cloudinit
    fi

    # Boot new VM with that image
    NOVA_OUTPUT=`nova boot  --flavor $VM_FLAVOR --image $IMAGE_ID --user-data ${BUILD}/cloudinit/$ROLENAME.cloudinit --security-groups $SECURITY_GROUP $VM_NAME`

    VM_ID=`echo $NOVA_OUTPUT | grep -ohe "id | [0-9a-f-]\{36\}" | cut -c 6-`

    echo "Getting private IP..."
    RETRIES=0
    while [ -z $IP ]; do
        IP=`nova show $VM_ID | grep "network" | cut -d "|" -f 3 | sed 's/ *$//g'`
        let RETRIES=RETRIES+1
        if [ "$RETRIES" == "9" ]; then
            echo "Failed getting private IP"
            break
        fi
        sleep 10
    done

    RETRIES=0
    while true; do
        echo "Getting unused floating IP..."
        FLOATING_IP=`nova floating-ip-list | grep "None" | grep -ohe "[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}" | head -n 1`
        nova add-floating-ip $VM_ID $FLOATING_IP

        if [ $? -eq 0 ]; then
            echo "Assigned floating IP $FLOATING_IP."
            SUMMARY=${SUMMARY}"$ROLENAME: $FLOATING_IP\n"
            break
        fi
        # Store ip configuration for postconfigure
        # This generate the same description as sf-lxc.yaml
        putip_to_yaml "${ROLENAME}" "${FLOATING_IP}"

        let RETRIES=RETRIES+1
        if [ "$RETRIES" == "9" ]; then
            break
        fi
        echo "Failed getting floating IP, will retry in 30 seconds"
        sleep 30
    done

    nova secgroup-add-rule $SECURITY_GROUP tcp 1 65535 "$FLOATING_IP/32"

    if [ "$ROLENAME" == "puppetmaster" ]; then
        generate_cloudinit
    fi
done

sf_postconfigure

echo -e $SUMMARY
