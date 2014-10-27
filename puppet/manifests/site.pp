node base {
  # these are imported from modules/base
  include disable_root_pw_login
  include ssh_keys
  include hosts
  include edeploy_client
  include postfix
  include monit
}

node default inherits base {
}

node /.*jenkins.*/ inherits base {
  include ssh_keys_jenkins
  include jenkins
  include jjb
  include zuul
  include cauth_client
  include bup
}

node /.*redmine.*/ inherits base {
  include redmine
  include cauth_client
}

node /.*gerrit.*/ inherits base {
  include ssh_keys_gerrit
  include gerrit
  include cauth_client
  include bup
}

node /.*mysql.*/ inherits base {
  include mysql
  include replication
  include bup
}

node /.*managesf.*/ inherits base {
  include managesf
  include cauth
  include cauth_client
  include commonservices-apache
  include commonservices-socat
  include etherpad
  include lodgeit
}
