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

  $fqdn = hiera('fqdn')
  $auth = hiera('authentication')
  $url = hiera('url')
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

  file {'/usr/bin/sfmanager':
    ensure => file,
    mode   => '0755',
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
}
