import 'base'

node default {
  # these are imported from base
  include ssh_keys
  include disable_root_pw_login
  include hosts
}
