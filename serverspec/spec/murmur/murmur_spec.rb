#
# Copyright (C) 2016 Red Hat
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

describe user('murmur') do
    it {
        should exist
    }
end

describe group('murmur') do
    it {
        should exist
    }
end

describe file('/etc/murmur.ini') do
    it {
        should be_file
        should be_owned_by 'murmur'
        should be_grouped_into 'murmur'
        should be_mode '400'
    }
end

describe service('murmurd') do
  it { should be_running }
end

describe port(64738) do
  it { should be_listening }
end
