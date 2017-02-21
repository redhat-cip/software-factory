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

describe user('gerrit') do
    it {
        should exist
        should belong_to_group 'gerrit'
        should have_home_directory '/var/lib/gerrit'
    }
end

describe file('/etc/gerrit') do
    it {
        should be_directory
        should be_owned_by 'gerrit'
    }
end

describe file('/etc/gerrit/gerrit.config') do
    it {
        should be_file
        should be_owned_by 'gerrit'
        should be_grouped_into 'gerrit'
        should be_mode '644'
    }
end

describe file('/etc/gerrit/secure.config') do
    it {
        should be_file
        should be_owned_by 'gerrit'
        should be_grouped_into 'gerrit'
        should be_mode '600'
    }
end

describe file('/etc/gerrit/ssh_host_rsa_key') do
    it {
        should be_file
        should be_owned_by 'gerrit'
        should be_grouped_into 'gerrit'
        should be_mode '400'
    }
end

# Gerrit itself
describe port(8000) do
  it { should be_listening }
end

describe port(29418) do
  it { should be_listening }
end
