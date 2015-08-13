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

class nodepool ($settings = hiera_hash('nodepool', '')) {

  $provider = "systemd"

  file { 'nodepool_service':
    path  => '/lib/systemd/system/nodepool.service',
    owner => 'jenkins',
    content => template('nodepool/nodepool.service.erb'),
  }

  file { '/var/run/nodepool':
    ensure  => directory,
    owner => 'jenkins',
  }

  file { '/var/log/nodepool/':
    ensure  => directory,
    owner => 'jenkins',
  }

  file { '/etc/nodepool':
    ensure  => directory,
    owner => 'jenkins',
  }

  file { '/etc/nodepool/scripts':
    ensure  => directory,
    owner => 'jenkins',
    require => [File['/etc/nodepool']]
  }

  file { '/usr/share/sf-nodepool':
    ensure  => directory,
    mode    => '0640',
    owner   => 'root',
    group   => 'root',
  }

  file { '/usr/share/sf-nodepool/base.sh':
    ensure => file,
    mode   => '0755',
    owner  => "root",
    group  => "root",
    source => 'puppet:///modules/nodepool/base.sh',
    require => [File['/usr/share/sf-nodepool']]
  }

  file { '/usr/share/sf-nodepool/sf_slave_setup.sh':
    ensure => file,
    mode   => '0755',
    owner  => "root",
    group  => "root",
    source => 'puppet:///modules/nodepool/sf_slave_setup.sh',
    require => [File['/usr/share/sf-nodepool']]
  }

  file { '/etc/nodepool/scripts/authorized_keys':
    owner => 'jenkins',
    mode   => '0600',
    source => 'puppet:///modules/nodepool/jenkins_rsa.pub',
    require => [File['/etc/nodepool/scripts']]
  }

  file { '/etc/nodepool/nodepool.yaml':
    owner => 'jenkins',
    content => template('nodepool/nodepool.yaml.erb'),
    require => [File['/etc/nodepool']]
  }

  file { '/etc/nodepool/nodepool.logging.conf':
    owner => 'jenkins',
    content => template('nodepool/nodepool.logging.conf'),
    require => [File['/etc/nodepool']]
  }

  service { 'nodepool':
    ensure      => running,
    enable      => true,
    hasrestart  => true,
    provider    => $provider,
    require     => [File['nodepool_service'],
                    File['/var/run/nodepool'],
                    File['/var/log/nodepool/'],
                    File['/etc/nodepool/nodepool.yaml'],
                    File['/etc/nodepool/nodepool.logging.conf'],
                    File['/etc/nodepool/scripts'],
                    ],
  }

}
