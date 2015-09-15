Package {
  allow_virtual => false,
}

$httpd_user = "apache"

stage { 'first':
  before => Stage["main"],
}

stage { 'last': }
Stage['main'] -> Stage['last']

node default {
}

node /.*puppetmaster.*/ {
  include sfbase
  include postfix
  include monit
  include edeploy_server
  include auto_backup
}

node /.*jenkins.*/ {
  include sfbase
  include postfix
  include monit
  include ssh_keys_jenkins
  include jenkins
  include jjb
  include zuul
  include nodepool
  include cauth_client
  include bup
}

node /.*redmine.*/ {
  include sfbase
  include postfix
  include monit
  include redmine
  include cauth_client
}

node /.*gerrit.*/ {
  include sfbase
  include postfix
  include monit
  include ssh_keys_gerrit
  include gerrit
  include bup
}

node /.*mysql.*/ {
  include sfbase
  include postfix
  include monit
  include mysql
  include bup
}

node /.*managesf.*/ {
  include sfbase
  include postfix
  include monit
  include apache
  include managesf
  include cauth
  include cauth_client
  include commonservices-apache
  include commonservices-socat
  include socat_gerrit
  include etherpad
  include lodgeit
  include replication
}

node /.*allinone.*/ {
  include sfbase
  include postfix
  include monit
 
  # Puppetmaster
  include edeploy_server
  include auto_backup

  # Jenkins
  include ssh_keys_jenkins
  include jenkins
  include jjb
  include zuul
  include nodepool
  include cauth_client
  include bup

  # Redmine
  include redmine
  include cauth_client

  # Gerrit
  include ssh_keys_gerrit
  include gerrit
  include bup

  # MySql
  include mysql
  include bup

  # Managesf gateway
  include apache
  include managesf
  include cauth
  include cauth_client
  include commonservices-apache
  include commonservices-socat
  include socat_gerrit
  include etherpad
  include lodgeit
  include replication
}
