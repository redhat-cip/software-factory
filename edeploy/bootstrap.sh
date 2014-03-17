#!/bin/bash

. bootstrap.conf
. ../function.sh

SUMMARY=""

function register_sf_admin_keypair {
    nova keypair-add --pub_key ~/.ssh/id_rsa.pub sf-admin-keypair
}

function select_flavor {
    if [ -z "$VM_FLAVOR" ]; then
        VM_FLAVOR="devstack-sf"
        echo "A special devstack flavor will be used ($VM_FLAVOR)."
    fi
    fvr_id=`nova flavor-list | grep $VM_FLAVOR | head -1 | cut -f 2 -d "|"`
    if [ -z "$fvr_id" ]; then
        if [ "$VM_FLAVOR" == "devstack-sf" ]; then
            # When running on devstack we need to save resourses
            # 1GB RAM, 3GB disk, 1 VCPU
            frv_id=`nova flavor-create devstack-sf auto 1024 3 1 | grep $VM_FLAVOR | head -1 | cut -f 2 -d "|"`
        else
            echo "Unable to find the right flavor ($VM_FLAVOR)"
            exit 1
        fi
    fi
    echo "Flavor ($VM_FLAVOR) id $fvr_id will be used."
}

function _add_in_security_group {
    local from_port=$1
    local to_port=$2
    local net=$3
    local out=''
    echo "Add in security group for ($from_port-$to_port) from: $net"
    out=`nova secgroup-add-rule $SECURITY_GROUP tcp $from_port $to_port $net 2>&1`
    [ "$?" != "0" ] && {
        echo $out | grep "already" > /dev/null 2>&1
        [ "$?" == "0" ] && {
            echo "Rule already exists."
        } || {
            echo "Unable to create the rule due to:"
            echo $out
            exit 1
        }
    }
}

function add_in_security_group {
    local out=''
    echo "Create security group $SECURITY_GROUP."
    out=`nova secgroup-create $SECURITY_GROUP "Software Factory" 2>&1`
    [ "$?" != "0" ] && {
        echo $out | grep "already" > /dev/null 2>&1
        [ "$?" == "0" ] && {
            echo "Security group $SECURITY_GROUP already exists."
        } || {
            echo "Unable to create security group $SECURITY_GROUP :"
            echo $out
            exit 1
        }
    }
    for network in $AUTHORIZED_NETS; do
        for port in $SERVICE_PORTS; do
            _add_in_security_group $port $port $network
        done
    done
}

function build_roles {
    local build_role_log="/tmp/build-roles.log"
    for rolename in $ROLES; do
        echo $rolename | grep jenkins-slave > /dev/null 2>&1
        if [ "$?" == "0" ]; then
            echo "Build role ${rolename} ... Nothing to do."
            return
        fi
        if [ "$RECREATE_ROLES" == "true" ]; then
            sudo rm -R $BUILD_ROLE_PATH/$rolename*
        fi
        if [ ! -e $BUILD_ROLE_PATH/$rolename-*.qcow2 ]; then
            echo "Build role ${rolename} ..."
            sudo make $rolename VIRTUALIZED=params.virt >> $build_role_log 2>&1
            if [ ! -e $BUILD_ROLE_PATH/$rolename-*.qcow2 ]; then
                echo "Build role ${rolename} fails (check $build_role_log)"
                exit 1
            fi
        else
            echo "Build role ${rolename} ... already built."
        fi
    done
}

function reserve_floating_ip {
    local roles_count=`echo $ROLES | wc -w`
    local avail_count=`nova floating-ip-list | grep -e None -e '|\s*-\s*|' | wc -l`
    while [[ $avail_count -le $role_count ]]; do
        echo "Not enough floating IPs available - request one"
        out=`nova floating-ip-create 2>&1`
        [ "$?" != "0" ] && {
            echo "Unable to request a floating IP :"
            echo $out
            exit 1
        }
        local avail_count=`nova floating-ip-list | grep None -e '|\s*-\s*|' | wc -l`
    done
    echo "Enough floating IPs available."
}

function upload_vm_image {
    local out=''
    echo "Upload role ${rolename} ..."
    path=$BUILD_ROLE_PATH/$rolename-$RELEASE.img.qcow2 
    echo $rolename | grep jenkins-slave > /dev/null 2>&1
    [ "$?" == 0 ] && {
        echo "Nothing to do we will use Jenkins image."
        return
    }
    image_id=`glance image-list | grep $vm_name  | cut -f 2 -d " "`
    if [ -z "$image_id" ]; then
        echo "Registering image in Glance..."
        out=`glance -v image-create --name="$vm_name" --container-format ovf --disk-format qcow2 < $path 2>&1`
        [ "$?" != "0" ] && {
            echo "Unable to upload image in glance :"
            echo $out
            exit 1
        }
        # Get image ID
        image_id=`echo $out | grep -ohe "id | [0-9a-f-]\{36\}" | cut -c 6-`
    else
        echo "Image for $rolename already exists."
    fi
}

function boot_vm_image {
    echo "Boot role ${rolename} ..."
    out=`nova list | grep $vm_name`
    [ "$?" == 0 ] && {
        vm_id=`echo $out | grep -ohe "[0-9a-f-]\{36\}" | head -1`
        echo "The virtual machine is already UP ($vm_id)."
        return
    }
    echo $rolename | grep jenkins-slave
    if [ "$?" == 0 ]; then
        cloudinit=jenkins.cloudinit
    else
        cloudinit=$rolename.cloudinit
    fi
    out=`nova boot --flavor $fvr_id --image $image_id --user-data ${BUILD}/cloudinit/$cloudinit --key-name sf-admin-keypair --security-groups $SECURITY_GROUP $vm_name 2>&1`
    [ "$?" != "0" ] && {
        echo "Unable to boot the virtual machine :"
        echo $out
        exit 1
    }
    vm_id=`echo $out | grep -ohe "id | [0-9a-f-]\{36\}" | cut -c 6-`
}

function check_vm_up {
    echo "Check role ${rolename} is up by getting private IP ..."
    retries=0
    while true; do
        priv_ip=`nova show $vm_id | grep "network" | cut -d "|" -f 3 | sed 's/ *$//g'`
        if [ -n "$priv_ip" ]; then
            echo "Node ${rolename} is UP."
            break
        fi
        let retries=retries+1
        if [ "$retries" == "9" ]; then
            echo "Failed getting private IP"
            echo "The virtual machine has failed to boot"
            exit 1
        fi
        sleep 10
    done
}

function add_vm_floating_ip {
    echo "Add a floating IP to ${rolename} ..."
    floating_ip=`nova floating-ip-list | grep "$vm_id" | head -1 | cut -f2 -d'|' | tr -d ' '`
    [ -n "$floating_ip" ] && {
        echo "A floating IP is already associated ($floating_ip)"
        return
    }
    floating_ip=`nova floating-ip-list | grep -e "None" -e "|\s*-\s*|" | grep -ohe "[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}" | head -n 1`
    out=`nova add-floating-ip $vm_id $floating_ip 2>&1`
    [ "$?" != "0" ] && {
        echo "Unable to associate floating IP to the virtual machine :"
        echo $out
        exit 1
    }
    retries=0
    while true; do
        nova list | grep -E "$vm_id.*$floating_ip" > /dev/null 2>&1
        [ "$?" == "0" ] && {
            echo "Floating IP association done ($floating_ip)"
            break
        }
        let retries=retries+1
        if [ "$retries" == "9" ]; then
            echo "Fail to assign floating IP to node ${rolename}. Exit."
            exit 1
        fi
        sleep 30
    done
}

function create_ssh_tunnel {
    for port in $SERVICE_PORTS; do
        if [[ $port -le 1024 ]]; then
            let listen_port=port+1024
        else
            listen_port=$port
        fi
        echo "Create tunnel from $local_ip:$listen_port to $DEVSTACK_SSH $floating_ip:$port"
        pkill -f "$local_ip:$listen_port"
        ssh -N -L $local_ip:$listen_port:$floating_ip:$port $DEVSTACK_SSH &
    done
}

function start {
    # This make sure ${BUILD} is clean
    new_build
    # This will build the role if needed
    build_roles
    # Register sf-admin-keypair
    register_sf_admin_keypair 
    # Select the VM flavor
    select_flavor
    # Be sure we have enough floating IPs
    reserve_floating_ip
    # Prepare security group
    add_in_security_group
    # VM boot
    ROLES="$ROLES"
    for rolename in $ROLES; do
        vm_name="$PREFIX-$rolename"
        echo "=== Process spawing of $vm_name ==="
        upload_vm_image
        boot_vm_image
        check_vm_up
        add_vm_floating_ip
        _add_in_security_group 1 65535 "$floating_ip/32"
        if [ -n "$DEVSTACK_SSH" ]; then
            last=`echo $floating_ip | cut -d. -f4`
            local_ip=127.0.1.$last
            create_ssh_tunnel
            putip_to_yaml_devstack "${rolename}" "${local_ip}"
        fi
        putip_to_yaml "${rolename}" "${floating_ip}"
        if [ "$rolename" == "puppetmaster" ]; then
            # We can create the cloudinit userdata for each VM
            # CLoudinit userdata will be set up with the puppet
            # master IP
            generate_cloudinit
        fi
        SUMMARY=${SUMMARY}"$rolename: $floating_ip ($local_ip)\n"
    done

    if [ -n "$DEVSTACK_SSH" ]; then
        sf_postconfigure "devstack"
    else
        sf_postconfigure
    fi

    echo -e $SUMMARY
}

function stop {
    for rolename in $ROLES; do
        vm_name="$PREFIX-$rolename"
        while true; do
            vm_id=`nova list | grep $vm_name | grep -ohe "[0-9a-f-]\{36\}" | head -1`
            [ -z "$vm_id" ] && break
            echo "Deleting virtual machine $vm_name with id $vm_id"
            nova delete $vm_id
            sleep 5
        done
    done
}

if [ "$1" == "start" ]; then
    stop
    start
fi
if [ "$1" == "stop" ]; then
    stop
fi
