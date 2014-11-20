#!/bin/bash

set -x

source ../functions.sh
. ./../../role_configrc

if [ -n "$FROMUPSTREAM" ]; then
    BUILT_ROLES=$UPSTREAM
else
    BUILT_ROLES=$INST
fi
SFCONFIGFILE=../sfconfig.yaml
DOMAIN=$(cat $SFCONFIGFILE | grep "^domain:" | cut -d' ' -f2)
suffix=$DOMAIN

### Modify here according to your configuration ###
# The default public key to use
key_name="thekey"
# flavor is used for managesf
flavor="m1.small"
# alt_flavor is used for puppetmaster, mysql, redmine, jenkins, gerrit (prefer flavor with at least 2 vCPUs and 2GB RAM)
#alt_flavor="standard.small"
alt_flavor=$flavor
ext_net_uuid="6c83db7b-480e-4198-bc69-88df6fd17e55"
# Network from TCP/22 is accessible
sg_admin_cidr="0.0.0.0/0"
# Network from ALL SF services are accessible
sg_user_cidr="0.0.0.0/0"
###################################################

jenkins_user_pwd=$(generate_random_pswd 8)
jenkins_master_url="jenkins.$suffix"

params="key_name=$key_name;instance_type=$flavor"
params="$params;alt_instance_type=$alt_flavor;suffix=$suffix"
params="$params;jenkins_user_pwd=$jenkins_user_pwd;jenkins_master_url=$jenkins_master_url"
params="$params;sg_admin_cidr=$sg_admin_cidr;sg_user_cidr=$sg_user_cidr"
params="$params;ext_net_uuid=$ext_net_uuid"

function get_params {
    puppetmaster_image_id=`glance image-show install-server-vm | grep "^| id" | awk '{print $4}'`
    params="$params;puppetmaster_image_id=$puppetmaster_image_id"
    sf_image_id=`glance image-show softwarefactory | grep "^| id" | awk '{print $4}'`
    params="$params;sf_image_id=$sf_image_id"
    sfconfigcontent=`cat $SFCONFIGFILE | base64 -w 0`
    params="$params;sf_config_content=$sfconfigcontent"
}

function register_images {
    for img in install-server-vm softwarefactory; do
        checksum=`glance image-show $img | grep checksum | awk '{print $4}'`
        if [ -z "$checksum" ]; then
            glance image-create --name $img --disk-format qcow2 --container-format bare \
                --progress --file $BUILT_ROLES/$img-${SF_VER}.img.qcow2
        fi
    done
}

function unregister_images {
    for img in install-server-vm softwarefactory; do
        checksum=`glance image-show $img | grep checksum | awk '{print $4}'`
        newchecksum=`cat $BUILT_ROLES/$img-${SF_VER}.img.qcow2.md5 | cut -d" " -f1`
        [ "$newchecksum" != "$checksum" ] && glance image-delete $img || true
    done
}

function start_stack {
    get_params
    heat stack-create --template-file sf.yaml -P "$params" SoftwareFactory
}

function delete_stack {
    heat stack-delete SoftwareFactory
}

function restart_stack {
    set +e
    delete_stack
    while true; do
        heat stack-list | grep "SoftwareFactory"
        [ "$?" != "0" ] && break
        sleep 2
    done
    set -e
    start_stack
}

function full_restart_stack {
    unregister_images
    sleep 10
    register_images
    restart_stack
}

[ -z "$1" ] && {
    echo "$0 register_images|unregister_images|start_stack|delete_stack|restart_stack|full_restart_stack"
}
[ -n "$1" ] && {
    case "$1" in
        register_images )
            register_images ;;
        unregister_images )
            unregister_images ;;
        start_stack )
            start_stack ;;
        delete_stack )
            delete_stack ;;
        restart_stack )
            restart_stack ;;
        full_restart_stack )
            full_restart_stack ;;
        * )
            echo "Not available option" ;;
    esac
}
