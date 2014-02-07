import 'disable_root_pw_login'
import 'ssh_keys'
import 'hosts'
import 'gerrit'

node default {
  include disable_root_pw_login
  include ssh_keys
  include hosts
  include gerrit
}
