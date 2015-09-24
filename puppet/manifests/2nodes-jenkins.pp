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
  class {'sfbase': stage => first }
  class {'bup': stage => first }
  include postfix
  include monit
  include cauth_client

  # Jenkins
  class {'ssh_keys_jenkins': stage => last }
  class {'jenkins': stage => last }
  # jjb also deploys zuul and nodepool
  class {'jjb': stage => last }
}
