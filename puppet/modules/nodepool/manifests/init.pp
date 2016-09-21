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

class nodepool {
  include ::systemctl

  $arch = hiera('roles')
  $jenkins_rsa_pub = hiera('jenkins_rsa_pub')
  $nodepool = hiera('nodepool')
  $fqdn = hiera('fqdn')
  $jenkins_host = "jenkins.${fqdn}"

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
    owner   => 'nodepool',
    source  => 'puppet:///modules/nodepool/nodepool.service',
    notify  => Exec['systemctl_reload'],
  }

  file { '/var/run/nodepool':
    ensure => directory,
    owner  => 'nodepool',
  }

  file { '/var/log/nodepool/':
    ensure => directory,
    owner  => 'nodepool',
    mode   => '0700',
  }

  file {'/etc/sysconfig/nodepool':
    content => template('graphite/statsd.environment.erb'),
  }

  file {'/opt/nodepool':
    ensure => directory,
    owner  => 'nodepool',
  }

  file { '/etc/nodepool':
    ensure => directory,
    owner  => 'nodepool',
  }

  file { '/etc/nodepool/scripts':
    ensure  => directory,
    owner   => 'nodepool',
    require => [File['/etc/nodepool']],
  }

  file { '/etc/nodepool/scripts/authorized_keys':
    owner   => 'nodepool',
    mode    => '0600',
    content => inline_template('<%= @jenkins_rsa_pub %>'),
    require => [File['/etc/nodepool/scripts']],
  }

  # This file will be used by the conf merger
  file { '/etc/nodepool/_nodepool.yaml':
    owner   => 'nodepool',
    content => template('nodepool/nodepool.yaml.erb'),
    require => [File['/etc/nodepool']],
  }

  file {'/etc/nodepool/logging.conf':
    source => 'puppet:///modules/nodepool/logging.conf',
    require => [File['/etc/nodepool/']],
  }


  service { 'nodepool':
    ensure     => $running,
    enable     => $enabled,
    hasrestart => true,
    require    => [File['nodepool_service'],
                    File['/var/run/nodepool'],
                    File['/var/log/nodepool/'],
                    File['/etc/nodepool/_nodepool.yaml'],
                    File['/etc/nodepool/scripts'],
                    File['/etc/nodepool/logging.conf'],
                    Exec['systemctl_reload'],
                    ],
  }

  bup::scripts{ 'nodepool_scripts':
    name           => 'nodepool',
    backup_script  => 'nodepool/backup.sh.erb',
    restore_script => 'nodepool/restore.sh.erb',
  }
}
