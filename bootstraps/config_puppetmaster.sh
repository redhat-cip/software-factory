#!/bin/bash

# This script configure the puppetmaster with passenger

set -x

lsb_release -id | head -1 | egrep "CentOS|rhel"
if [ "$?" == "0" ]; then
    dist="centos"
else
    dist="debian"
fi

set -e

FQDN=$(hostname -f)

service puppetmaster stop
case $dist in
    debian)
        service apache2 stop
        ;;
    centos)
        service httpd stop
        ;;
    *)
        echo "$dist not supported !"
        exit 1
        ;;
esac

cat > /etc/puppet/puppet.conf << EOF
[main]
logdir=/var/log/puppet
vardir=/var/lib/puppet
ssldir=/var/lib/puppet/ssl
rundir=/var/run/puppet
factpath=\$vardir/lib/facter
templatedir=\$confdir/templates
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

case $dist in
    debian)
        PM_A_CONF=/etc/apache2/sites-available/puppetmaster
        ;;
    centos)
        PM_A_CONF=/etc/httpd/conf.d/puppetmaster.conf
        cp /etc/httpd/conf.d/puppetmaster.conf.disabled $PM_A_CONF
        ;;
esac

sed -i -e "s!SSLCertificateFile.*!SSLCertificateFile /var/lib/puppet/ssl/certs/${FQDN}.pem!" $PM_A_CONF 
sed -i -e "s!SSLCertificateKeyFile.*!SSLCertificateKeyFile /var/lib/puppet/ssl/private_keys/${FQDN}.pem!" $PM_A_CONF

rm -rf /var/lib/puppet/ssl && puppet cert generate ${FQDN}

case $dist in
    debian)
        cp /var/lib/puppet/ssl/private_keys/${FQDN}.pem /etc/puppetdb/ssl/key.pem \
	    && chown puppetdb:puppetdb /etc/puppetdb/ssl/key.pem
        cp /var/lib/puppet/ssl/certs/${FQDN}.pem /etc/puppetdb/ssl/cert.pem \
	    && chown puppetdb:puppetdb /etc/puppetdb/ssl/cert.pem
        cp /var/lib/puppet/ssl/certs/ca.pem /etc/puppetdb/ssl/ca.pem \
	    && chown puppetdb:puppetdb /etc/puppetdb/ssl/ca.pem
        echo '. /etc/default/locale' | tee --append /etc/apache2/envvars
        puppet resource service puppetmaster ensure=stopped enable=false
        a2ensite puppetmaster
        service apache2 start
        ;;
    centos)
        puppet resource service puppetmaster ensure=stopped enable=false
        systemctl start httpd.service
        ;;
esac


