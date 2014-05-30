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

class jjb ($settings = hiera_hash('jenkins', ''),
            $gerrit = hiera_hash('gerrit', ''),
            $redmine = hiera_hash('redmine', '')) {

  require hosts

  file {'/etc/jenkins_jobs/jenkins_jobs.ini':
    ensure  => file,
    mode    => '0400',
    owner   => 'jenkins',
    group   => 'nogroup',
    content => template('jjb/jenkins_jobs.ini.erb'),
    require => User['jenkins'],
  }

  file {'/root/gerrit_admin_rsa':
    ensure => file,
    mode   => '0400',
    owner  => "root",
    group  => "root",
    source => 'puppet:///modules/jjb/gerrit_admin_rsa',
  }

  file {'/root/init-config-repo.sh':
    ensure  => file,
    mode    => '0540',
    owner   => 'root',
    group   => 'root',
    content => template('jjb/init-config-repo.sh.erb'),
  }
  
  file {'/usr/local/jenkins':
    ensure   => directory,
    mode     => '0540',
    owner    => 'root',
    group    => 'root',
  }

  file {'/usr/local/jenkins/slave_scripts':
    ensure   => directory,
    mode     => '0540',
    owner    => 'root',
    group    => 'root',
    require  => File['/usr/local/jenkins']
  }

  file {'/usr/local/jenkins/slave_scripts/kick.sh':
    ensure   => file,
    mode     => '0540',
    owner    => 'root',
    group    => 'root',
    content  => template('jjb/kick.sh.erb'),
    require  => File['/usr/local/jenkins/slave_scripts'],
  }
  
  exec {'init_config_repo':
    command => '/root/init-config-repo.sh',
    path    => '/usr/sbin/:/usr/bin/:/bin/:/usr/local/bin',
    logoutput => true,
    provider => shell,
    require => [File['/root/init-config-repo.sh'],
                File['/root/gerrit_admin_rsa']],
  }

  exec {'kick_jjb':
    command => '/usr/local/jenkins/slave_scripts/kick.sh',
    path    => '/usr/sbin/:/usr/bin/:/bin/:/usr/local/bin',
    logoutput => true,
    provider => shell,
    require => [Exec['init_config_repo'],
                Service['jenkins'],
                File['/etc/jenkins_jobs/jenkins_jobs.ini'],
                File['/usr/local/jenkins/slave_scripts/kick.sh']],
  }
}
