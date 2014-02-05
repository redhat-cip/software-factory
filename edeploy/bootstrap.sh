#!/bin/bash
SECURITY_GROUPS="SF-security"
TIMESTAMP=`date +"%Y%m%d"`
PREFIX="edeploy-$TIMESTAMP-"
ROLES="mysql redmine"
VM_FLAVOR="10"
RELEASE="D7-H.1.0.0"
HOSTS_YAML="../puppet/hiera/hosts.yaml"


echo -e "hosts:\n  localhost:\n    ip: 127.0.0.1" > $HOSTS_YAML

for ROLENAME in $ROLES; do
	VM_NAME="$PREFIX$ROLENAME"
	
	if [ "$1" == "recreate" ]; then	
		rm /var/lib/debootstrap/install/D7-H.1.0.0/$ROLENAME-D7-H.1.0.0.img*
		rm /var/lib/debootstrap/install/D7-H.1.0.0/$ROLENAME.done
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

	# Boot new VM with that image
	NOVA_OUTPUT=`nova boot  --key-name cschwede --flavor $VM_FLAVOR --image $IMAGE_ID --user-data ../cloudinit/$ROLENAME.cloudinit --security-groups $SECURITY_GROUPS $VM_NAME`

	VM_ID=`echo $NOVA_OUTPUT | grep -ohe "id | [0-9a-f-]\{36\}" | cut -c 6-`
	
	echo "Getting private IP..."
	RETRIES=0
	while [ -z $IP ]; do
		IP=`nova show $VM_ID | grep "nova network" | cut -d "|" -f 3 | sed 's/ *$//g'`
		let RETRIES=RETRIES+1
		if [ "$RETRIES" == "9" ]; then
			echo "Failed getting private IP"
			break
		fi
		sleep 5
	done 

	echo "Getting unused floating IP..."
	FLOATING_IP=`nova floating-ip-list | grep "-" | grep -ohe "[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}" | head -n 1`
	nova add-floating-ip $VM_ID $FLOATING_IP
	echo "Assigned floating IP $FLOATING_IP."

	
	echo "  $ROLENAME.priv:" >> $HOSTS_YAML
	echo "    ip: $IP" >> $HOSTS_YAML
	
	echo "  $ROLENAME.pub:" >> $HOSTS_YAML
	echo "    ip: $FLOATING_IP" >> $HOSTS_YAML

done 
