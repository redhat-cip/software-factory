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

describe user('zuul') do
    it {
        should exist
    }
end

describe group('zuul') do
    it {
        should exist
    }
end

describe file('/etc/zuul/zuul.conf') do
    it {
        should be_file
        should be_grouped_into 'zuul'
        should be_mode '440'
        }
end

describe file('/etc/zuul/layout.yaml') do
    it {
        should be_file
        should be_owned_by 'zuul'
        should be_grouped_into 'zuul'
        should be_mode '644'
    }
end

describe service('zuul') do
  it { should be_running }
end

describe service('zuul-merger') do
  it { should be_running }
end

describe port(4730) do # gearman server port
  it { should be_listening }
end

describe port(8001) do # zuul server port
  it { should be_listening }
end
