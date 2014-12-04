require 'serverspec'
require 'pathname'
require 'net/ssh'
require 'yaml'

include SpecInfra::Helper::Ssh
include SpecInfra::Helper::DetectOS
include Serverspec::Helper::Properties

properties = YAML.load_file('hosts.yaml')

RSpec.configure do |c|
  c.sudo_password = ENV['SUDO_PASSWORD']
  c.host  = c.exclusion_filter()[:host]
  options = Net::SSH::Config.for(c.host)
  user    = ENV['USER'] || Etc.getlogin
  c.ssh   = Net::SSH.start(c.host, user, options)
  c.os    = backend.check_os
  set_property properties[ENV['ROLE']]
end
