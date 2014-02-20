#!/bin/bash
TIMESTAMP=`date +"%Y%m%d"`
PREFIX="edeploy-$TIMESTAMP-"
VM_FLAVOR="10"
ROLES="puppetmaster mysql ldap redmine jenkins gerrit "
RELEASE="D7-H.1.0.0"
HOSTS_YAML="../puppet/hiera/hosts.yaml"
SUMMARY=""

echo -e "hosts:\n  localhost:\n    ip: 127.0.0.1" > $HOSTS_YAML


cp ../serverspec/hosts.yaml.tpl ../serverspec/hosts.yaml
echo > hosts

SECURITY_GROUP="${PREFIX}sg"
nova secgroup-create $SECURITY_GROUP "Software Factory"
***REMOVED***
nova secgroup-add-rule $SECURITY_GROUP tcp 22 22 46.231.128.220/24
nova secgroup-add-rule $SECURITY_GROUP tcp 80 80 0.0.0.0/0 
nova secgroup-add-rule $SECURITY_GROUP tcp 8080 8080 0.0.0.0/0 

PUPPETMASTER_IP=""

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

    if [ "$PUPPETMASTER_IP" != "" ]; then
        sed -i -e "s#.*puppetmaster.pub.*# - echo $PUPPETMASTER_IP puppetmaster.pub >> /etc/hosts#g" ../cloudinit/$ROLENAME.cloudinit
    fi

	# Boot new VM with that image
	NOVA_OUTPUT=`nova boot  --flavor $VM_FLAVOR --image $IMAGE_ID --user-data ../cloudinit/$ROLENAME.cloudinit --security-groups $SECURITY_GROUP $VM_NAME`

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

		let RETRIES=RETRIES+1
		if [ "$RETRIES" == "9" ]; then
			break
		fi
		echo "Failed getting floating IP, will retry in 30 seconds"
		sleep 30
    done

	echo "  $ROLENAME.pub:" >> $HOSTS_YAML
	echo "    ip: $FLOATING_IP" >> $HOSTS_YAML
	echo "    host_aliases: [\'sf-$ROLENAME\', \'$ROLENAME.pub\']" >> $HOSTS_YAML
    sed -i -e "s/$ROLENAME\_ip/$FLOATING_IP/g" ../serverspec/hosts.yaml

    echo "$FLOATING_IP" >> hosts
    nova secgroup-add-rule $SECURITY_GROUP tcp 1 65535 "$FLOATING_IP/32"

    # First role is puppetmaster -> first IP is from puppetmaster
    if [ "$PUPPETMASTER_IP" == "" ]; then
        PUPPETMASTER_IP=$FLOATING_IP
    fi

    ssh-keygen -f "$HOME/.ssh/known_hosts" -R $FLOATING_IP
    
    RETRIES=0
    while true; do
	    echo "Starting ssh-keyscan on $FLOATING_IP"
        KEY=`ssh-keyscan -H $FLOATING_IP`
        if [ "$KEY" != ""  ]; then
            echo $KEY >> $HOME/.ssh/known_hosts
            break
        fi

		let RETRIES=RETRIES+1
		if [ "$RETRIES" == "9" ]; then
			break
		fi
		echo "ssh-keyscan on $FLOATING_IP failed, will retry in 30 seconds"
		sleep 30
    done
    
    scp $HOSTS_YAML $PUPPETMASTER_IP:/etc/puppet/hiera/hosts.yaml
done 

echo -e $SUMMARY
