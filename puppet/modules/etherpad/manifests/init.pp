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

class etherpad ($etherpad = hiera_hash('etherpad', '')) {

  user { 'etherpad':
    name => 'etherpad',
    ensure => 'present',
    home => '/var/www/etherpad-lite-1.4.0',
    require => Group['etherpad'],
  }

  group { 'etherpad':
    ensure => present,
  }

  file { '/var/www/etherpad-lite-1.4.0':
    ensure  => directory,
    owner   => 'etherpad',
    group   => 'etherpad',
    require => [User['etherpad'],
                Group['etherpad']],
  }

  file { '/var/log/etherpad':
    ensure  => directory,
    owner   => 'etherpad',
    group   => 'etherpad',
    require => [User['etherpad'],
                Group['etherpad']],
  }

  file { '/var/www/etherpad-lite-1.4.0/run.sh':
    ensure  => present,
    owner   => 'etherpad',
    group   => 'etherpad',
    mode    => '0740',
    source  => 'puppet:///modules/etherpad/run.sh',
    require => File['/var/www/etherpad-lite-1.4.0'],
  }

  file { '/etc/init.d/etherpad-lite':
    ensure  => present,
    owner   => 'etherpad',
    group   => 'etherpad',
    mode    => '0740',
    source  => 'puppet:///modules/etherpad/etherpad-lite',
  }

  file { '/var/www/etherpad-lite-1.4.0/settings.json':
    ensure   => present,
    owner    => 'etherpad',
    group    => 'etherpad',
    mode     => '0640',
    content  => template('etherpad/settings.json.erb'),
    require  => File['/var/www/etherpad-lite-1.4.0'],
    notify   => Service[etherpad-lite],
  }

  exec {'change_owner':
    command => 'chown -R etherpad:etherpad /var/www/etherpad-lite-1.4.0',
    path    => '/usr/sbin/:/usr/bin/:/bin/',
    require => [File['/var/www/etherpad-lite-1.4.0/run.sh'],
                File['/etc/init.d/etherpad-lite'],
                File['/var/www/etherpad-lite-1.4.0/settings.json']]
  }

  service {'etherpad-lite':
    ensure     => running,
    enable     => true,
    hasrestart => true,
    hasstatus  => true,
    require    => [File['/var/log/etherpad'],
                   Exec['change_owner']],
  }

}
