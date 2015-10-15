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

class jjb ($gerrit = hiera('gerrit')) {

  require hosts
  require jenkins
  require zuul
  require nodepool

  $fqdn = hiera('fqdn')
  $auth = hiera('authentication')
  $url = hiera('url')
  $gerrit_admin_rsa = hiera('gerrit_admin_rsa')
  $gerrit_host = "gerrit.${fqdn}"

  $jenkins_password = hiera('creds_jenkins_user_password')
  $jenkins_username = 'jenkins'

  file {'/etc/jenkins_jobs/jenkins_jobs.ini':
    ensure  => file,
    mode    => '0400',
    owner   => 'jenkins',
    group   => 'jenkins',
    content => template('jjb/jenkins_jobs.ini.erb'),
    require => User['jenkins'],
  }

  file {'/root/gerrit_admin_rsa':
    ensure  => file,
    mode    => '0400',
    owner   => 'root',
    group   => 'root',
    content => inline_template('<%= @gerrit_admin_rsa %>'),
  }

  file {'/usr/bin/sfmanager':
    ensure => file,
    mode   => '0755',
  }

  file {'/root/init-config-repo.sh':
    ensure  => file,
    mode    => '0540',
    owner   => 'root',
    group   => 'root',
    content => template('jjb/init-config-repo.sh.erb'),
  }

  file {'/usr/share/sf-jjb':
    ensure => directory,
    mode   => '0750',
    owner  => 'root',
    group  => 'root',
  }

  file {'/usr/local/bin/yaml-merger.py':
    ensure  => file,
    mode    => '0755',
    owner   => 'root',
    group   => 'root',
    require => File['/usr/share/sf-jjb'],
    source  => 'puppet:///modules/jjb/yaml-merger.py',
  }

  file {'/usr/share/sf-jjb/projects.yaml':
    ensure  => file,
    mode    => '0640',
    owner   => 'root',
    group   => 'root',
    require => File['/usr/share/sf-jjb'],
    content => template('jjb/projects.yaml.erb'),
  }

  file {'/usr/share/sf-jjb/sf_jjb_conf.yaml':
    ensure  => file,
    mode    => '0640',
    owner   => 'root',
    group   => 'root',
    require => File['/usr/share/sf-jjb'],
    content => template('jjb/sf_jjb_conf.yaml.erb'),
  }

  file {'/usr/local/jenkins':
    ensure => directory,
    mode   => '0555',
    owner  => 'root',
    group  => 'root',
  }

  file {'/usr/local/jenkins/slave_scripts':
    ensure  => directory,
    mode    => '0555',
    owner   => 'root',
    group   => 'root',
    require => File['/usr/local/jenkins'],
  }

  file {'/usr/local/jenkins/slave_scripts/kick.sh':
    ensure  => file,
    mode    => '0540',
    owner   => 'root',
    group   => 'root',
    content => template('jjb/kick.sh.erb'),
    require => File['/usr/local/jenkins/slave_scripts'],
  }

  exec {'init_config_repo':
    command   => '/root/init-config-repo.sh',
    path      => '/usr/sbin/:/usr/bin/:/bin/:/usr/local/bin',
    logoutput => true,
    provider  => shell,
    require   => [File['/root/init-config-repo.sh'],
                File['/usr/share/sf-jjb/projects.yaml'],
                File['/usr/share/sf-jjb/sf_jjb_conf.yaml'],
                File['/usr/share/sf-zuul/layout.yaml'],
                File['/usr/share/sf-nodepool/base.sh'],
                File['/usr/share/sf-nodepool/sf_slave_setup.sh'],
                File['/usr/share/sf-nodepool/images.yaml'],
                File['/usr/share/sf-nodepool/labels.yaml'],
                File['/usr/bin/sfmanager'],
                File['/root/gerrit_admin_rsa']],
    creates   => '/usr/share/config.init.done',
  }

  exec {'kick_jjb':
    command   => '/usr/local/jenkins/slave_scripts/kick.sh',
    path      => '/usr/sbin/:/usr/bin/:/bin/:/usr/local/bin',
    logoutput => true,
    provider  => shell,
    require   => [Exec['init_config_repo'],
                File['/etc/jenkins_jobs/jenkins_jobs.ini'],
                File['/usr/local/jenkins/slave_scripts/kick.sh']],
    creates   => '/root/config.kicked',
  }
}
