#!/bin/bash

set -x

source ../functions.sh

VERS=D7-H.0.9.0
BUILT_ROLES=/var/lib/sf
SFCONFIGFILE=../sfconfig.yaml
DOMAIN=$(cat $SFCONFIGFILE | grep domain | cut -d' ' -f2)

### Modify here according to your configuration ###
# The default public key to use
key_name="fbo"
# flavor is used for managesf
flavor="m1.small"
# alt_flavor is used for puppetmaster, mysql, redmine, jenkins, gerrit (prefer flavor with at least 2 vCPUs and 2GB RAM)
#alt_flavor="standard.small"
alt_flavor=$flavor
suffix="tests.dom"
ext_net_uuid="1013481d-c86b-4a9d-8d3d-e5d9448749fc"
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
    mysql_image_id=`glance image-show mysql | grep "^| id" | awk '{print $4}'`
    params="$params;mysql_image_id=$mysql_image_id"
    slave_image_id=`glance image-show slave | grep "^| id" | awk '{print $4}'`
    params="$params;slave_image_id=$slave_image_id"
    sfconfigcontent=`cat $SFCONFIGFILE | base64 -w 0`
    params="$params;sf_config_content=$sfconfigcontent"
}

function register_images {
    for img in install-server-vm mysql slave softwarefactory; do
        checksum=`glance image-show $img | grep checksum | awk '{print $4}'`
        if [ -z "$checksum" ]; then
            glance image-create --name $img --disk-format qcow2 --container-format bare \
                --progress --file $BUILT_ROLES/roles/install/${VERS}/$img-*.img
        fi
    done
}

function unregister_images {
    for img in install-server-vm mysql slave softwarefactory; do
        checksum=`glance image-show $img | grep checksum | awk '{print $4}'`
        newchecksum=`cat $BUILT_ROLES/roles/install/${VERS}/$img-*.img.md5 | cut -d" " -f1`
        [ "$newchecksum" != "$checksum" ] && glance image-delete $img
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
    delete_stack || true
    while true; do
        heat stack-list | grep "SoftwareFactory"
        [ "$?" != "0" ] && break
        sleep 2
    done
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
