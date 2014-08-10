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
  include jenkins
  include jjb
  include zuul
  include cauth_client
}

node /.*redmine.*/ inherits base {
  include redmine
  include cauth_client
}

node /.*gerrit.*/ inherits base {
  include gerrit
  include cauth_client
}

node /.*mysql.*/ inherits base {
  include mysql
  include replication
}

node /.*ldap.*/ inherits base {
  include ldap
}

node /.*managesf.*/ inherits base {
  include managesf
  include cauth
  include cauth_client
}

node /.*commonservices.*/ inherits base {
  include commonservices-apache
  include commonservices-socat
  include etherpad
  include lodgeit
  include cauth_client
}
