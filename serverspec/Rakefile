require 'rake'
require 'serverspec'
require 'rspec/core/rake_task'
require 'yaml'

hosts = YAML.load_file('hosts.yaml')

task :spec    => 'spec:all'

namespace :spec do

  task :all => hosts.keys.map {|role| 'spec:' + role.split('.')[0] }
  task :default => :all

  hosts.keys.each do |target|
    original_target = target == "_default" ? target[1..-1] : target
    desc "Run serverspec tests to #{original_target}"
    RSpec::Core::RakeTask.new(target.to_sym) do |t|
      ENV['TARGET_HOST'] = original_target
      t.pattern = 'spec/{' + hosts[target][:roles].join(',') + '}/*_spec.rb'
      t.rspec_opts = "-t ~host:#{hosts[target][:hostname]}"
    end
  end
end
