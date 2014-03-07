#!/bin/bash

BUILD="../build"

# TODO: Should be moved in other place maybe a config file for bootstrap scripts ?
GERRIT_ADMIN=fabien.boucher
GERRIT_ADMIN_MAIL=fabien.boucher@enovance.com

#### Configuration generation
function new_build {
    rm -Rf ${BUILD}/
    mkdir ${BUILD}
    echo "hosts:" > ${BUILD}/sf-host.yaml
}

function putip_to_yaml {
    cat << EOF >> ${BUILD}/sf-host.yaml
  -
    name: sf-$1
    address: $2
EOF
}

function getip_from_yaml {
    cat ${BUILD}/sf-host.yaml  | grep -A 1 -B 1 "name: sf-$1$" | grep 'address' | cut -d: -f2 | sed 's/ *//g'
}

function generate_cloudinit {
    OUTPUT=${BUILD}/cloudinit
    PUPPETMASTER_IP=$(getip_from_yaml puppetmaster)
    rm -Rf ${OUTPUT}
    mkdir -p ${OUTPUT}
    for i in ../cloudinit/*.cloudinit; do
        cat $i | sed "s#PUPPETMASTER#${PUPPETMASTER_IP}#g" > ${OUTPUT}/$(basename $i)
    done
}

function generate_hiera {
    OUTPUT=${BUILD}/hiera
    rm -Rf ${OUTPUT}
    mkdir -p ${OUTPUT}

    # Hosts
    echo -e "hosts:\n  localhost:\n    ip: 127.0.0.1" > ${OUTPUT}/hosts.yaml
    for role in $ROLES; do
        echo "  ${role}.pub:" >> ${OUTPUT}/hosts.yaml
        echo "    ip: $(getip_from_yaml ${role})" >> ${OUTPUT}/hosts.yaml
        echo "    host_aliases: [\'sf-${role}\', \'${role}.pub\']" >> ${OUTPUT}/hosts.yaml
    done

    # Jenkins ssh key
    JENKINS_PUB="$(cat ${OUTPUT}/../data/jenkins_rsa.pub | cut -d' ' -f2)"
    cat ../puppet/hiera/ssh.yaml | sed "s#JENKINS_PUB_KEY#${JENKINS_PUB}#" > ${OUTPUT}/ssh.yaml

    # Gerrit service key
    GERRIT_SERV_PUB="$(cat ${OUTPUT}/../data/gerrit_service_rsa.pub | cut -d' ' -f2)"
    cat ../puppet/hiera/gerrit.yaml | sed "s#GERRIT_SERV_PUB_KEY#ssh-rsa ${GERRIT_SERV_PUB}#" > ${OUTPUT}/gerrit.yaml

    # Gerrit Jenkins pub key
    sed -i "s#JENKINS_PUB_KEY#ssh-rsa ${JENKINS_PUB}#" ${OUTPUT}/gerrit.yaml

    # Gerrit Admin pubkey,mail,login
    GERRIT_ADMIN_PUB_KEY="$(cat ${OUTPUT}/../data/gerrit_admin_rsa.pub | cut -d' ' -f2)"
    sed -i "s#GERRIT_ADMIN_PUB_KEY#ssh-rsa ${GERRIT_ADMIN_PUB_KEY}#" ${OUTPUT}/gerrit.yaml
    sed -i "s#GERRIT_ADMIN_NAME#${GERRIT_ADMIN}#" ${OUTPUT}/gerrit.yaml
    sed -i "s#GERRIT_ADMIN_MAIL#${GERRIT_ADMIN_MAIL}#" ${OUTPUT}/gerrit.yaml

    # Gerrit Redmine API key
    # TODO Will be randomly generated
    REDMINE_API_KEY="7f094d4e3e327bbd3f67279c95c193825e48f59e"
    sed -i "s#REDMINE_API_KEY#${REDMINE_API_KEY}#" ${OUTPUT}/gerrit.yaml

    # Redmine API key
    cat ../puppet/hiera/redmine.yaml | sed "s#REDMINE_API_KEY#${REDMINE_API_KEY}#" > ${OUTPUT}/redmine.yaml

    # Redmine Credencials ID
    # TODO: Will be randomly generated
    JENKINS_CREDS_ID="a6feb755-3493-4635-8ede-216127d31bb0"
    cat ../puppet/hiera/jenkins.yaml | sed "s#JENKINS_CREDS_ID#${JENKINS_CREDS_ID}#" > ${OUTPUT}/jenkins.yaml
}

function generate_keys {
    OUTPUT=${BUILD}/data
    rm -Rf ${OUTPUT}
    mkdir -p ${OUTPUT}
    ssh-keygen -N '' -f ${OUTPUT}/jenkins_rsa
    ssh-keygen -N '' -f ${OUTPUT}/gerrit_service_rsa
    ssh-keygen -N '' -f ${OUTPUT}/gerrit_admin_rsa
}


#### Post configuration
function post_configuration_etc_hosts {
    # Make sure /etc/hosts is up-to-date
    for role in ${ROLES}; do
        HOST_LINE="$(getip_from_yaml ${role}) sf-${role}"
        grep "sf-${role}$" /etc/hosts > /dev/null
        if [ $? == 0 ]; then
            cat /etc/hosts | grep -v "sf-${role}$" | sudo tee /etc/hosts.new > /dev/null
            sudo mv /etc/hosts.new /etc/hosts
        fi
        echo ${HOST_LINE} | sudo tee -a /etc/hosts > /dev/null
    done
}

function post_configuration_knownhosts {
    # Update known_hosts file and make sure vm are available
    echo "[+] Update local knownhosts file"
    for role in ${ROLES}; do
        ssh-keygen -f "$HOME/.ssh/known_hosts" -R sf-${role} > /dev/null 2>&1
        ssh-keygen -f "$HOME/.ssh/known_hosts" -R $(getip_from_yaml ${role}) > /dev/null 2>&1
        RETRIES=0
        echo " [+] Starting ssh-keyscan on sf-${role}"
        while true; do
            KEY=`ssh-keyscan sf-${role} 2> /dev/null`
            if [ "$KEY" != ""  ]; then
                ssh-keyscan sf-${role} >> "$HOME/.ssh/known_hosts" 2> /dev/null
                echo "  -> sf-${role} is up!"
                break
            fi

            let RETRIES=RETRIES+1
            [ "$RETRIES" == "6" ] && break
            echo "  [E] ssh-keyscan on sf-${role} failed, will retry in 5 seconds"
            sleep 10
        done
    done
}

function post_configuration_puppet_apply {
    echo "[+] Running one last puppet agent"
    for role in ${ROLES}; do
        echo " [+] sf-${role}"
        ssh root@sf-${role} puppet agent --test
    done
}

function generate_serverspec {
    OUTPUT=${BUILD}/serverspec
    rm -Rf ${OUTPUT}
    mkdir -p ${OUTPUT}
    cp ../serverspec/hosts.yaml.tpl ${OUTPUT}/hosts.yaml
    for role in ${ROLES}; do
        sed -i -e "s/${role}_ip/$(getip_from_yaml ${role})/g" ${OUTPUT}/hosts.yaml
    done
}

function post_configuration_update_hiera {
    scp ${BUILD}/hiera/*.yaml root@sf-puppetmaster:/etc/puppet/hiera/
}

function post_configuration_ssh_keys {
    # jenkins ssh key
    ssh root@sf-jenkins mkdir /var/lib/jenkins/.ssh/
    scp ${BUILD}/data/jenkins_rsa root@sf-jenkins:/var/lib/jenkins/.ssh/id_rsa
    ssh root@sf-jenkins chown -R jenkins /var/lib/jenkins/.ssh/
    ssh root@sf-jenkins chmod 400 /var/lib/jenkins/.ssh/id_rsa

    # gerrit ssh key
    scp ${BUILD}/data/gerrit_service_rsa root@sf-gerrit:/home/gerrit/ssh_host_rsa_key
    scp ${BUILD}/data/gerrit_service_rsa.pub root@sf-gerrit:/home/gerrit/ssh_host_rsa_key.pub
    ssh root@sf-gerrit chown gerrit:gerrit /home/gerrit/ssh_host_rsa_key
    ssh root@sf-gerrit chown gerrit:gerrit /home/gerrit/ssh_host_rsa_key.pub
}

function post_configuration_jenkins_scripts {
    # Update jenkins slave scripts
    for host in "sf-jenkins" "sf-jenkins-slave01" "sf-jenkins-slave02"; do
        ssh root@${host} mkdir -p /usr/local/jenkins/slave_scripts/
        scp ../data/jenkins_slave_scripts/* root@${host}:/usr/local/jenkins/slave_scripts/
    done
}

function sf_postconfigure {
    # ${BUILD}/sf-host.yaml must be present and filled with roles ip
    generate_serverspec
    generate_keys
    generate_hiera
    post_configuration_etc_hosts
    post_configuration_knownhosts
    post_configuration_ssh_keys
    post_configuration_update_hiera
    post_configuration_puppet_apply
    post_configuration_jenkins_scripts
}
