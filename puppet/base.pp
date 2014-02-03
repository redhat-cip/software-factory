class ssh_keys ($keys = hiera_hash("ssh_keys")) {
  create_resources('ssh_authorized_key', $keys)
} 

class disable_root_pw_login {
  user {'root':
    ensure     => present,
    managehome => true,
    password   => '*',  # disables login without password
  }
}

class hosts ($hosts = hiera_hash("hosts"))  {
  create_resources('host', $hosts)
}
