class ssh_keys ($keys = hiera_hash("ssh_keys")) {
  create_resources('ssh_authorized_key', $keys)
} 
