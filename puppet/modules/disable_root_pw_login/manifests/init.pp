class disable_root_pw_login {
  user {'root':
    ensure     => present,
    managehome => true,
    password   => '*',  # disables login without password
  }
}
