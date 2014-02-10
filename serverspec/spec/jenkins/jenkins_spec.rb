require 'spec_helper'

describe user('jenkins') do
    it {
        should exist 
    }
end

describe file('/var/lib/jenkins/config.xml') do
    it {
        should be_file
        should be_owned_by 'jenkins'
        should be_grouped_into 'nogroup'
        should be_mode '644'
    }
end

describe file('/etc/jenkins_jobs/jenkins_jobs.ini') do
    it {
        should be_file
        should be_owned_by 'root'
        should be_grouped_into 'root'
        should be_mode '400'
    }
end

describe package('jenkins') do
    it { should be_installed }
end

describe service('jenkins') do
  it { should be_enabled }
end

describe port(8080) do
  it { should be_listening }
end

