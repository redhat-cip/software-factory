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
        should have_home_directory '/home/gerrit'
    }
end

describe file('/home/gerrit/site_path') do
    it {
        should be_directory
        should be_owned_by 'gerrit' 
    }
end

describe file('/home/gerrit/site_path/etc') do
    it {
        should be_directory
        should be_owned_by 'gerrit'
    }
end

describe file('/home/gerrit/site_path/bin') do
    it {
        should be_directory
        should be_owned_by 'gerrit'
    }
end

describe file('/home/gerrit/site_path/static') do
    it {
        should be_directory
        should be_owned_by 'gerrit'
    }
end

describe file('/home/gerrit/site_path/hooks') do
    it {
        should be_directory
        should be_owned_by 'gerrit'
    }
end

describe file('/home/gerrit/site_path/lib') do
    it {
        should be_directory
        should be_owned_by 'gerrit'
    }
end

describe file('/home/gerrit/site_path/etc/gerrit.config') do
    it {
        should be_file
        should be_owned_by 'gerrit'
        should be_grouped_into 'gerrit'
        should be_mode '644'
    }
end

describe file('/home/gerrit/site_path/etc/secure.config') do
    it {
        should be_file
        should be_owned_by 'gerrit'
        should be_grouped_into 'gerrit'
        should be_mode '600'
    }
end

describe file('/home/gerrit/site_path/etc/ssh_host_rsa_key') do
    it {
        should be_file
        should be_owned_by 'gerrit'
        should be_grouped_into 'gerrit'
        should be_mode '600'
    }
end

describe file('/home/gerrit/site_path/etc/ssh_host_rsa_key.pub') do
    it {
        should be_file
        should be_owned_by 'gerrit'
        should be_grouped_into 'gerrit'
        should be_mode '644'
    }
end

describe file('/root/gerrit-firstuser-init.sql') do
    it {
        should be_file
        should be_mode '644'
    }
end

describe file('/root/gerrit-firstuser-init.sh') do
    it {
        should be_file
        should be_mode '700'
    }
end

describe file('/root/gerrit-set-default-acl.sh') do
     it {
        should be_file
        should be_mode '700'
    }
end

describe file('/root/gerrit-set-jenkins-user.sh') do
    it {
        should be_file
        should be_mode '700'
    }
end


describe file('/home/gerrit/gerrit.war') do
    it {
        should be_file
        should be_owned_by 'gerrit'
        should be_grouped_into 'gerrit'
        should be_mode '644'
    }
end

describe file('/home/gerrit/site_path/lib/mysql-connector-java-5.1.21.jar') do
    it {
        should be_file
        should be_owned_by 'gerrit'
        should be_grouped_into 'gerrit'
    }
end
  
describe file('/home/gerrit/site_path/lib/bcprov-jdk15on-149.jar') do
    it {
        should be_file
        should be_owned_by 'gerrit'
        should be_grouped_into 'gerrit'
    }
end

describe file('/home/gerrit/site_path/lib/bcpkix-jdk15on-149.jar') do
    it {
        should be_file
        should be_owned_by 'gerrit'
        should be_grouped_into 'gerrit'
    }
end

if os[:family] == 'RedHat7'
  describe file('/lib/systemd/system/gerrit.service') do
      it {
          should be_file
      }
  end
else
  describe file('/etc/init.d/gerrit') do
      it {
          should be_linked_to '/home/gerrit/site_path/bin/gerrit.sh'
      }
  end
end

describe service('gerrit') do
  it { should be_enabled }
end

# Gerrit itself
describe port(8080) do
  it { should be_listening }
end

describe port(29418) do
  it { should be_listening }
end
