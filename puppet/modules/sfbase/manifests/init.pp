#
class sfbase() {
# these are imported from modules/base
include ::disable_root_pw_login
include ::ssh_keys
include ::hosts
include ::edeploy_client
include ::ntpserver
include ::https_cert
}
