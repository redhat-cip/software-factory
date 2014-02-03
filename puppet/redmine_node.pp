import 'base'
import 'redmine'

node default {
  # these are imported from base
  include disable_root_pw_login
  include ssh_keys
  include hosts

  include redmine
}
