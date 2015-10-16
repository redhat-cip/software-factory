#
# Copyright (C) 2015 Red Hat
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

class nodepool {

  $jenkins_rsa_pub = hiera('jenkins_rsa_pub')
  $nodepool = hiera('nodepool')
  $fqdn = hiera('fqdn')
  $url = hiera('url')

  $jenkins_host = "jenkins.${fqdn}"
  $jenkins_password = hiera('creds_jenkins_user_password')
  $nodepool_mysql_address = "mysql.${fqdn}"
  $nodepool_sql_password = hiera('creds_nodepool_sql_pwd')

  if $nodepool['disabled'] {
    $running = false
    $enabled = false
  }
  else {
    $running = true
    $enabled = true
  }

  file { 'nodepool_service':
    path    => '/lib/systemd/system/nodepool.service',
    owner   => 'jenkins',
    content => template('nodepool/nodepool.service.erb'),
  }

  file { '/var/run/nodepool':
    ensure => directory,
    owner  => 'jenkins',
  }

  file { '/var/log/nodepool/':
    ensure => directory,
    owner  => 'jenkins',
  }

  file { '/etc/nodepool':
    ensure => directory,
    owner  => 'jenkins',
  }

  file { '/etc/nodepool/scripts':
    ensure  => directory,
    owner   => 'jenkins',
    require => [File['/etc/nodepool']],
  }

  file { '/usr/share/sf-nodepool':
    ensure => directory,
    mode   => '0640',
    owner  => 'root',
    group  => 'root',
  }

  file { '/usr/local/bin/sf-nodepool-conf-merger.py':
    ensure => file,
    mode   => '0755',
    owner  => 'root',
    group  => 'root',
    source => 'puppet:///modules/nodepool/sf-nodepool-conf-merger.py',
  }

  file { '/usr/local/bin/sf-nodepool-conf-update.sh':
    ensure => file,
    mode   => '0755',
    owner  => 'root',
    group  => 'root',
    content => template('nodepool/sf-nodepool-conf-update.sh.erb'),
  }

  file { '/usr/share/sf-nodepool/base.sh':
    ensure  => file,
    mode    => '0755',
    owner   => 'root',
    group   => 'root',
    source  => 'puppet:///modules/nodepool/base.sh',
    require => [File['/usr/share/sf-nodepool']],
  }

  file { '/usr/share/sf-nodepool/sf_slave_setup.sh':
    ensure  => file,
    mode    => '0755',
    owner   => 'root',
    group   => 'root',
    source  => 'puppet:///modules/nodepool/sf_slave_setup.sh',
    require => [File['/usr/share/sf-nodepool']],
  }

  file { '/usr/share/sf-nodepool/images.yaml':
    ensure  => file,
    mode    => '0755',
    owner   => 'root',
    group   => 'root',
    source  => 'puppet:///modules/nodepool/images.yaml',
    require => [File['/usr/share/sf-nodepool']],
  }

  file { '/usr/share/sf-nodepool/labels.yaml':
    ensure  => file,
    mode    => '0755',
    owner   => 'root',
    group   => 'root',
    source  => 'puppet:///modules/nodepool/labels.yaml',
    require => [File['/usr/share/sf-nodepool']],
  }

  file { '/etc/nodepool/scripts/authorized_keys':
    owner   => 'jenkins',
    mode    => '0600',
    content => inline_template('<%= @jenkins_rsa_pub %>'),
    require => [File['/etc/nodepool/scripts']],
  }

  file { '/etc/nodepool/nodepool.logging.conf':
    owner   => 'jenkins',
    source  => 'puppet:///modules/nodepool/nodepool.logging.conf',
    require => [File['/etc/nodepool']],
  }

  # This file will be used by the conf merger
  file { '/etc/nodepool/_nodepool.yaml':
    owner   => 'jenkins',
    content => template('nodepool/nodepool.yaml.erb'),
    require => [File['/etc/nodepool']],
    notify  => Exec['build_etc_nodepool'],
  }

  exec { 'build_etc_nodepool':
    command     => '/usr/local/bin/sf-nodepool-conf-update.sh apply',
    logoutput   => true,
    onlyif      => '/usr/bin/test -f /root/config.kicked',
    require     => Exec['kick_jjb'],
    refreshonly => true,
  }

  service { 'nodepool':
    ensure     => $running,
    enable     => $enabled,
    hasrestart => true,
    require    => [File['nodepool_service'],
                    File['/var/run/nodepool'],
                    File['/var/log/nodepool/'],
                    File['/etc/nodepool/_nodepool.yaml'],
                    File['/etc/nodepool/nodepool.logging.conf'],
                    File['/etc/nodepool/scripts'],
                    ],
  }

}
