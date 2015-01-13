#!/bin/bash

set -x

source ../functions.sh
. ./../../role_configrc
. conf

generate_sfconfig
if [ -n "$FROMUPSTREAM" ]; then
    BUILT_ROLES=$UPSTREAM
else
    BUILT_ROLES=$INST
fi

FORMAT=${FORMAT:-qcow2}

STACKNAME=${STACKNAME:-SoftwareFactory}
DOMAIN=$(cat $SFCONFIGFILE | grep "^domain:" | cut -d' ' -f2)
suffix=$DOMAIN

[ -n "${NOVA_KEYNAME}" ] && key_name="${NOVA_KEYNAME}" || {
    [ -n "${HEAT_TENANT}" ] && key_name="${HEAT_TENANT}"
}

jenkins_user_pwd=$(generate_random_pswd 8)

params="key_name=$key_name;suffix=$suffix"

params="$params;puppetmaster_flavor=$puppetmaster_flavor"
params="$params;mysql_flavor=$mysql_flavor"
params="$params;managesf_flavor=$managesf_flavor"
params="$params;gerrit_flavor=$gerrit_flavor"
params="$params;redmine_flavor=$redmine_flavor"
params="$params;jenkins_flavor=$jenkins_flavor"
params="$params;slave_flavor=$slave_flavor"

params="$params;puppetmaster_root_size=$puppetmaster_root_size"
params="$params;mysql_root_size=$mysql_root_size"
params="$params;managesf_root_size=$managesf_root_size"
params="$params;gerrit_root_size=$gerrit_root_size"
params="$params;redmine_root_size=$redmine_root_size"
params="$params;jenkins_root_size=$jenkins_root_size"
params="$params;slave_root_size=$slave_root_size"

params="$params;jenkins_user_pwd=$jenkins_user_pwd"
params="$params;sg_admin_cidr=$sg_admin_cidr;sg_user_cidr=$sg_user_cidr"
params="$params;ext_net_uuid=$ext_net_uuid"

function waiting_stack_deleted {
    wait_for_statement "heat stack-show ${STACKNAME} &> /dev/null" 1
}

function wait_for_statement {
    local STATEMENT=$1
    local EXPECT_RETURN_CODE=${2-0}
    local MAX_RETRY=${3-40}
    local SLEEP_TIME=${4-5}
    while true; do
        eval "${STATEMENT}" &> /dev/null
        if [ "$?" == "${EXPECT_RETURN_CODE}" ]; then
            break
        fi
        sleep ${SLEEP_TIME}
        let MAX_RETRY=MAX_RETRY-1
        if [ "${MAX_RETRY}" == 0 ]; then
            echo "Following statement didn't happen: [$STATEMENT]"
            return 1
        fi
    done
}

function get_params {
    puppetmaster_image_id=`glance image-show ${STACKNAME}_install-server-vm | grep "^| id" | awk '{print $4}'`
    params="$params;puppetmaster_image_id=$puppetmaster_image_id"
    sf_image_id=`glance image-show ${STACKNAME}_softwarefactory | grep "^| id" | awk '{print $4}'`
    params="$params;sf_image_id=$sf_image_id"
    sfconfigcontent=`cat $SFCONFIGFILE | base64 -w 0`
    params="$params;sf_config_content=$sfconfigcontent"
}

function convert_to_raw {
    if [ "$FORMAT" == "raw" ]; then
        for img in install-server-vm softwarefactory; do
            checksum=`cat $BUILT_ROLES/$img-${SF_VER}.img.qcow2.md5 | cut -d" " -f1`
            [ -f "$BUILT_ROLES/$img-${SF_VER}-$checksum.raw" ] && continue || {
                sudo rm -f $BUILT_ROLES/$img-${SF_VER}-*.raw # remove previous images previously converted and no longer relevant
                sudo qemu-img convert -f qcow2 -O raw $BUILT_ROLES/$img-${SF_VER}.img.qcow2 $BUILT_ROLES/$img-${SF_VER}-$checksum.raw
                echo $(cat  $BUILT_ROLES/$img-${SF_VER}-$checksum.raw| md5sum - | cut -d " " -f1) | sudo tee $BUILT_ROLES/$img-${SF_VER}-$checksum.raw.md5
            }
        done
    fi
}

function register_images {
    for img in install-server-vm softwarefactory; do
        checksum=`glance image-show ${STACKNAME}_$img | grep checksum | awk '{print $4}'`
        if [ -z "$checksum" ]; then
            if [ "$FORMAT" == "raw" ]; then
                glance image-create --name ${STACKNAME}_$img --disk-format raw --container-format bare \
                    --progress --file $BUILT_ROLES/$img-${SF_VER}-*.raw
            else
                glance image-create --name ${STACKNAME}_$img --disk-format qcow2 --container-format bare \
                    --progress --file $BUILT_ROLES/$img-${SF_VER}.img.qcow2
            fi
        fi
    done
}

function unregister_images {
    for img in install-server-vm softwarefactory; do
        checksum=`glance image-show ${STACKNAME}_$img | grep checksum | awk '{print $4}'`
        if [ "$FORMAT" == "raw" ]; then
            checks=`cat $BUILT_ROLES/$img-${SF_VER}.img.qcow2.md5 | cut -d" " -f1`
            newchecksum=`cat $BUILT_ROLES/$img-${SF_VER}-$checks.raw.md5`
        else
            newchecksum=`cat $BUILT_ROLES/$img-${SF_VER}.img.qcow2.md5 | cut -d" " -f1`
        fi
        [ "$newchecksum" != "$checksum" ] && glance image-delete ${STACKNAME}_$img || true
    done
}

function delete_images {
    for img in install-server-vm softwarefactory; do
        glance image-delete ${STACKNAME}_$img || true
    done
}

function start_stack {
    get_params
    heat stack-create --template-file sf.yaml -P "$params" $STACKNAME
}

function delete_stack {
    heat stack-delete ${STACKNAME} || true
    waiting_stack_deleted || {
        # Sometime delete failed and needs to be retriggered...
        heat stack-delete ${STACKNAME} || true
        waiting_stack_deleted || {
            echo "After 2 attempts the stack has not been deleted ! so exit !"
            exit 1
        }
    }
}

function restart_stack {
    delete_stack
    start_stack
}

function full_restart_stack {
    delete_stack
    unregister_images
    sleep 10
    register_images
    start_stack
}

[ -z "$1" ] && {
    echo "$0 register_images|unregister_images|start_stack|delete_stack|restart_stack|full_restart_stack"
}
[ -n "$1" ] && {
    case "$1" in
        register_images )
            convert_to_raw
            register_images
            ;;
        unregister_images )
            convert_to_raw
            unregister_images
            ;;
        start_stack )
            start_stack
            ;;
        delete_stack )
            delete_stack
            ;;
        delete_images )
            delete_images
            ;;
        restart_stack )
            restart_stack
            ;;
        full_restart_stack )
            convert_to_raw
            full_restart_stack
            ;;
        * )
            echo "Not available option" ;;
    esac
}
