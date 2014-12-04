require 'rake'
require 'rspec/core/rake_task'
require 'yaml'

hosts = YAML.load_file('hosts.yaml')

desc "Run serverspec to all hosts"
task :spec => 'serverspec:all'

namespace :serverspec do
  task :all => hosts.keys.map {|role| 'serverspec:' + role.split('.')[0] }
  hosts.keys.each do |role|
    desc "Run serverspec to #{role}"
    RSpec::Core::RakeTask.new(role.split('.')[0].to_sym) do |t|
      ENV['SUDO_PASSWORD'] = hosts[role][:sudo_password]
      ENV['USER'] = hosts[role][:username]
      ENV['ROLE'] = role
      t.pattern = 'spec/{' + hosts[role][:roles].join(',') + '}/*_spec.rb'
      t.rspec_opts = "-t ~host:#{hosts[role][:hostname]}"
    end
  end
end
