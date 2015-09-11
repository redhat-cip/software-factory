class sfbase() {
# these are imported from modules/base
include disable_root_pw_login
include ssh_keys
include hosts
include edeploy_client
include postfix
include monit
# TODO: workaround for testing
#if $virtual != 'lxc' {
#  include ntpserver
#}
include https_cert
}
