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

describe user('storyboard') do
    it { should exist }
end

describe group('storyboard') do
    it { should exist }
end

describe file('/etc/storyboard/storyboard.conf') do
    it {
        should be_file
        should be_owned_by 'storyboard'
        should be_grouped_into 'storyboard'
        should be_mode '400'
    }
end

describe service('storyboard') do
  it { should be_running }
end

describe port(20000) do
  it { should be_listening }
end
