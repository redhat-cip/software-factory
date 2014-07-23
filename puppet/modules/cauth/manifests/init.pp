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

class cauth ($cauth = hiera_hash('cauth', ''),
             $redmine = hiera_hash('redmine', '')) {
  file { '/var/www/cauth/':
    ensure  => directory,
    owner   => 'www-data',
    group   => 'www-data',
    mode    => '0640'
  }

  file { '/var/www/cauth/keys':
    ensure  => directory,
    owner   => 'root',
    group   => 'root',
    mode    => '0655'
  }

  file { '/srv/cauth_keys/privkey.pem':
    ensure => present,
    owner => 'root',
    group => 'root',
    mode  => '0444',
    source => 'puppet:///modules/cauth/privkey.pem'
  }

  file { '/var/www/cauth/config.py':
    ensure  => present,
    owner   => 'www-data',
    group   => 'www-data',
    mode    => '0640',
    content => template('cauth/cauth-config.py.erb'),
    require => File['/var/www/cauth/'],
    replace => true,
  }

  file {'/etc/apache2/sites-available/cauth':
    ensure => file,
    mode   => '0640',
    owner  => 'www-data',
    group  => 'www-data',
    content=> template('cauth/cauth.site.erb'),
  }

  exec {'enable_cauth_site':
    command => 'a2ensite cauth',
    path    => '/usr/sbin/:/usr/bin/:/bin/',
    require => [File['/etc/apache2/sites-available/cauth'],
                File['/var/www/cauth/config.py']],
    notify => Service[apache2],
  }
}
