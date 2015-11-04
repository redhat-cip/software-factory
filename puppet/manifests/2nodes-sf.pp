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
  include ::commonservices_apache
  include ::commonservices_socat
  include ::etherpad
  include ::lodgeit
  include ::replication

  include ::edeploy_server
  include ::auto_backup

  # graphite, statsd and grafana
  include ::graphite
  include ::grafana
}
