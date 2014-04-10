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

class managesf ($gerrit = hiera_hash('gerrit', ''), $redmine = hiera_hash('redmine', '')) {

  package { 'apache2':
    ensure => present,
  }

  package { 'libapache2-mod-wsgi':
    ensure => present,
  }

  service {'apache2':
    ensure  => running,
    require => [Package['apache2'], Package['libapache2-mod-wsgi']],
  }

  file { '/var/www/managesf/':
    ensure  => present,
    owner   => 'www-data',
    group   => 'www-data',
    mode    => '0640'
  }

  file { '/var/www/managesf/config.py':
    ensure  => present,
    owner   => 'www-data',
    group   => 'www-data',
    mode    => '0640',
    content => template('managesf/config.py.erb'),
    require => File['/var/www/managesf/'],
    replace => true,
  }

  file { '/var/www/managesf/gerrit_admin_rsa':
    ensure => present,
    owner  => 'www-data',
    group  => 'www-data',
    mode   => '0400',
    require => File['/var/www/managesf/'],
  }

  file {'/etc/apache2/sites-available/managesf':
    ensure => file,
    mode   => '0640',
    owner  => 'www-data',
    group  => 'www-data',
    source =>'puppet:///modules/managesf/managesf',
    notify => Service[apache2],
  }

  file { '/etc/apache2/sites-enabled/000-default':
    ensure => absent,
  }

  exec {'enable_managesf_site':
    command => 'a2ensite managesf',
    path    => '/usr/sbin/:/usr/bin/:/bin/',
    require => [File['/etc/apache2/sites-available/managesf'], File['/var/www/managesf/config.py']],
    notify => Service[apache2],
  }
}
