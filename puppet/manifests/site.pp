node base {
  # these are imported from modules/base
  include disable_root_pw_login
  include ssh_keys
  include hosts
  include ssmtp
}

node default inherits base {
}

node /.*jenkins\..*/ inherits base {
  include jenkins
  include jjb
}

node /.*jenkins-slave.*/ inherits base {
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

