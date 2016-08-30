#
# Copyright (C) 2014 eNovance SAS <licensing@enovance.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
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
        should be_grouped_into 'jenkins'
        should be_mode '644'
    }
end

describe file('/etc/jenkins_jobs/jenkins_jobs.ini') do
    it {
        should be_file
        should be_owned_by 'jenkins'
        should be_mode '400'
    }
end

describe package('jenkins') do
    it { should be_installed }
end

describe port(8080) do
  it { should be_listening }
end
