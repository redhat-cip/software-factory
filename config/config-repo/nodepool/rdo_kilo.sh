#!/bin/bash

RDO_RELEASE=https://repos.fedorapeople.org/repos/openstack/openstack-kilo/rdo-release-kilo-1.noarch.rpm

. sf_rdo_slave_setup.sh


# fix hiera issue (BZ#1284978)
#sudo yum install -y \
#    http://buildlogs.centos.org/centos/7/cloud/x86_64/openstack-kilo/openstack-packstack-2015.1-0.13.dev1616.g5526c38.el7.noarch.rpm            \
#    http://buildlogs.centos.org/centos/7/cloud/x86_64/openstack-kilo/openstack-packstack-puppet-2015.1-0.13.dev1616.g5526c38.el7.noarch.rpm


