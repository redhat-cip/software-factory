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

describe "monit" do
    let(:title) { 'monit' }

    context 'monit' do
        it {
            should contain_package('monit')
            should contain_service('monit')
            should contain_file('/etc/monit/monitrc')
            should contain_file('/etc/monit/conf.d/rootfs')
            should contain_file('/etc/monit/conf.d/system')
        }
    end
end
