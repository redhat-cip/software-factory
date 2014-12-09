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

class monit ($settings = hiera_hash('monit', '')) {

  require hosts

  $provider = "systemd"

  package { 'monit':
    ensure => present,
  }

  file { '/etc/monit':
    ensure  => directory,
    require => Package['monit']
  }

  file { '/etc/monit/conf.d':
    ensure  => directory,
    require => Package['monit']
  }

  file { '/etc/monit/monitrc':
    ensure  => present,
    content => template('monit/monitrc'),
    require => [Package['monit'], File['/etc/monit']],
    replace => true,
  }

  service { 'monit':
    ensure      => running,
    enable      => true,
    hasrestart  => true,
    provider    => $provider,
    require     => Package['monit'],
    subscribe   => File['/etc/monit/monitrc'],
  }

  file { '/etc/monit/conf.d/rootfs':
    ensure  => present,
    source  => 'puppet:///modules/monit/rootfs',
    require => [Package['monit'], File['/etc/monit/conf.d']],
    notify  => Service['monit'],
  }

  file { '/etc/monit/conf.d/system':
    ensure  => present,
    source  => 'puppet:///modules/monit/system',
    require => [Package['monit'], File['/etc/monit/conf.d']],
    notify  => Service['monit'],
  }

}
