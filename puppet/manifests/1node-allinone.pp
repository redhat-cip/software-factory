Package {
  allow_virtual => false,
}

stage { 'first':
  before => Stage['main'],
}

node default {
  # Base
  class {'::sfbase': stage => first }
  class {'::sfmysql': stage => first }
  include ::postfix
  include ::backup

  # Gerrit
  include ::gerrit

  # Redmine
  include ::redmine

  # Managesf
  include ::managesf
  include ::cauth
  include ::gateway
  include ::etherpad
  include ::lodgeit
  include ::replication

  include ::edeploy_server
  include ::auto_backup

  # CI
  include ::jenkins
  include ::nodepool
  include ::zuul

  # Statsd
  include ::sfgnocchi
  include ::grafana

  # Gerritbot
  include ::gerritbot
}
