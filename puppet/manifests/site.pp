Package {
  allow_virtual => false,
}

$httpd_user = "apache"

node default {
}

node /.*puppetmaster.*/ {
  include sfbase
  include edeploy_server
  include auto_backup
}

node /.*jenkins.*/ {
  include sfbase
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
  include redmine
  include cauth_client
}

node /.*gerrit.*/ {
  include sfbase
  include ssh_keys_gerrit
  include gerrit
  include bup
}

node /.*mysql.*/ {
  include sfbase
  include mysql
  include bup
}

node /.*managesf.*/ {
  include sfbase
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
