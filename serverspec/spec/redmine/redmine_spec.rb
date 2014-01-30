require 'spec_helper'

describe package('redmine') do
  it { should be_installed }
end


