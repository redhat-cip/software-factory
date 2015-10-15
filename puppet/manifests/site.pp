Package {
  allow_virtual => false,
}

$httpd_user = 'apache'

stage { 'first':
  before => Stage['main'],
}

stage { 'last': }
Stage['main'] -> Stage['last']

node default {
  class {'::sfbase': stage => first }
  class {'::mysql': stage => first }
  class {'::bup': stage => first }

  include ::postfix
  include ::monit

  # Gerrit
  include ::ssh_keys_gerrit
  include ::gerrit
  include ::bup

  # Redmine
  include ::redmine

  # Managesf
  include ::apache
  include ::managesf
  include ::cauth
  include ::cauth_client
  include ::commonservices-apache
  include ::etherpad
  include ::lodgeit
  include ::replication

  include ::edeploy_server
  include ::auto_backup

  # Jenkins
  class {'::ssh_keys_jenkins': stage => last }
  class {'::jenkins': stage => last }
  # jjb also deploys zuul and nodepool
  class {'::jjb': stage => last }
}

node /.*allinone.*/ {
  include ::sfbase
  include ::postfix
  include ::monit

  # Puppetmaster
  include ::edeploy_server
  include ::auto_backup

  # Jenkins
  include ::ssh_keys_jenkins
  include ::jenkins
  include ::jjb
  include ::zuul
  include ::nodepool
  include ::cauth_client
  include ::bup

  # Redmine
  include ::redmine
  include ::cauth_client

  # Gerrit
  include ::ssh_keys_gerrit
  include ::gerrit
  include ::bup

  # MySql
  include ::mysql
  include ::bup

  # Managesf gateway
  include ::apache
  include ::managesf
  include ::cauth
  include ::cauth_client
  include ::commonservices-apache
  include ::etherpad
  include ::lodgeit
  include ::replication
}
