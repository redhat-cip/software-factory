#!/bin/bash

# This script configure the puppetmaster with passenger

set -x

set -e

FQDN=$(hostname -f)

service puppetmaster stop
service httpd stop

cat > /etc/puppet/puppet.conf << EOF
[main]
logdir=/var/log/puppet
vardir=/var/lib/puppet
ssldir=/var/lib/puppet/ssl
rundir=/var/run/puppet
factpath=\$vardir/lib/facter
environmentpath = \$confdir/environments
autosign=true

[master]
# These are needed when the puppetmaster is run by passenger
# and can safely be removed if webrick is used.
ssl_client_header = SSL_CLIENT_S_DN
ssl_client_verify_header = SSL_CLIENT_VERIFY

[agent]
pluginsync=true
certname=${FQDN}
server=${FQDN}
EOF

PM_A_CONF=/etc/httpd/conf.d/puppetmaster.conf
cp /etc/httpd/conf.d/puppetmaster.conf.disabled $PM_A_CONF

sed -i -e "s!SSLCertificateFile.*!SSLCertificateFile /var/lib/puppet/ssl/certs/${FQDN}.pem!" $PM_A_CONF
sed -i -e "s!SSLCertificateKeyFile.*!SSLCertificateKeyFile /var/lib/puppet/ssl/private_keys/${FQDN}.pem!" $PM_A_CONF

rm -rf /var/lib/puppet/ssl && puppet cert generate ${FQDN}

puppet resource service puppetmaster ensure=stopped enable=false
systemctl start httpd.service
