node base {
  # these are imported from modules/base
  include disable_root_pw_login
  include ssh_keys
  include hosts
  include edeploy_client
  include ssmtp
  include monit
}

node default inherits base {
}

node /.*jenkins-swarm-slave.*/ inherits base {
  include jenkins-swarm-slave
}

node /.*jenkins.*/ inherits base {
  include jenkins
  include jjb
}

node /.*redmine.*/ inherits base {
  include redmine
}

node /.*gerrit.*/ inherits base {
  include gerrit
}

node /.*mysql.*/ inherits base {
  include mysql
}

node /.*ldap.*/ inherits base {
  include ldap
}

node /.*managesf.*/ inherits base {
  include managesf
}

node /.*commonservices.*/ inherits base {
  include commonservices-apache
  include etherpad
}
