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

class postfix ($settings = hiera_hash('postfix', '')) {

  require hosts

  $provider = "systemd"

  group { 'postfix':
    ensure => present,
  }

  group { 'postdrop':
    ensure => present,
  }

  user { 'postfix':
    ensure  => present,
    gid     => 'postfix',
    require => Group['postfix'],
  }

  package { 'postfix':
    ensure => 'installed',
    require => [User['postfix'], Group['postfix']],
  }

  exec { '/etc/mailname':
    command => 'hostname --fqdn > /etc/mailname',
    unless   => "/usr/bin/grep `hostname --fqdn` /etc/mailname",
    path    => '/usr/sbin/:/usr/bin/:/bin/',
  }

  file { '/etc/postfix':
    ensure  => directory,
    require => Package['postfix']
  }

  file { '/etc/postfix/main.cf':
    ensure  => present,
    content => template('postfix/main.cf'),
    require => [Package['postfix'], File['/etc/postfix']],
    replace => true,
  }

  service { 'postfix':
    ensure      => running,
    enable      => true,
    hasrestart  => true,
    provider    => $provider,
    require     => [Package['postfix'], Exec['/etc/mailname']],
    subscribe   => File['/etc/postfix/main.cf'],
  }

  file { '/etc/monit/conf.d/postfix':
    ensure  => present,
    content => template('postfix/monit.erb'),
    require => [Package['monit'], File['/etc/monit/conf.d']],
    notify  => Service['monit'],
  }

}
