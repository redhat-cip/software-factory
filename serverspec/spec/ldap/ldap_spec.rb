require 'spec_helper'

describe package('slapd') do
  it { should be_installed }
end

describe port(389) do
  it { should be_listening }
end
