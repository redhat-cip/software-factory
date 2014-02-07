require 'spec_helper'

describe user('gerrit') do
    it {
        should exist 
        should belong_to_group 'gerrit'
        should have_home_directory '/home/gerrit'
        should have_login_shell '/bin/bash'
    }
end

describe package('openjdk-7-jre') do
    it { should be_installed }
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
  
describe file('/home/gerrit/site_path/lib/bcprov-jdk16-144.jar') do
    it {
        should be_file
        should be_owned_by 'gerrit'
        should be_grouped_into 'gerrit'
    }
end

describe file('/etc/init.d/gerrit') do
    it {
        should be_linked_to '/home/gerrit/site_path/bin/gerrit.sh'
        should be_owned_by 'gerrit'
        should be_grouped_into 'gerrit'
    }
end

describe file('/etc/default/gerritcodereview') do
    it {
        should be_file
        should be_owned_by 'gerrit'
        should be_grouped_into 'gerrit'
        should be_mode '444'
        should contain 'GERRIT_SITE=/home/gerrit/site_path'
    }
end

describe service('gerrit') do
  it { should be_enabled }
end
