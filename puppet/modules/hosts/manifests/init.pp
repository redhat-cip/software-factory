class hosts ($hosts = hiera_hash("hosts"))  {
  create_resources('host', $hosts)
}
