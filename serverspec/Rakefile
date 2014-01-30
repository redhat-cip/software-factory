require 'rake'
require 'rspec/core/rake_task'

RSpec::Core::RakeTask.new(:spec) do |t|
  t.pattern = 'spec/' + ENV['ROLE'] + '/*_spec.rb'
end
