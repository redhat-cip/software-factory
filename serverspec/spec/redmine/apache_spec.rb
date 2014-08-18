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

if os[:family] == 'RedHat7'
  describe package('httpd') do
    it { should be_installed }
  end
  describe file('/etc/httpd/conf.d/redmine.conf') do
    it { should be_file }
    it { should contain "DocumentRoot /usr/share/redmine/public" }
  end
  describe service('httpd') do
    it { should be_enabled }
    it { should be_running }
  end
else
  describe package('apache2') do
    it { should be_installed }
  end
  describe package('libapache2-mod-passenger') do
    it { should be_installed }
  end
  describe file('/etc/apache2/sites-enabled/redmine') do
    it { should be_file }
    it { should contain "DocumentRoot /usr/share/redmine/public" }
  end
  describe service('apache2') do
    it { should be_enabled }
    it { should be_running }
  end
end

describe port(80) do
  it { should be_listening }
end

