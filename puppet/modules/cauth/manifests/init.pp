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
             $redmine = hiera_hash('redmine', ''),
             $gerrit = hiera_hash('gerrit', ''),
             $mysql = hiera_hash('mysql', '')) {

  $http = "httpd"
  $httpd_user = "apache"

  file {'/etc/httpd/conf.d/cauth.conf':
    ensure => file,
    mode   => '0640',
    owner  => $httpd_user,
    group  => $httpd_user,
    source => 'puppet:///modules/cauth/cauth.site',
    notify => Service['webserver'],
  }

  file { '/var/www/cauth/':
    ensure  => directory,
    owner  => $httpd_user,
    group  => $httpd_user,
    mode    => '0640'
  }

  file { '/var/lib/cauth/':
    ensure  => directory,
    owner  => $httpd_user,
    group  => $httpd_user,
    mode    => '0750'
  }

  file { '/var/www/cauth/keys':
    ensure  => directory,
    owner   => 'root',
    group   => 'root',
    mode    => '0655',
    require => File['/var/www/cauth/'],
  }

  file { '/var/log/cauth/':
    ensure  => directory,
    owner   => $httpd_user,
    group   => $httpd_user,
    mode    => '0750',
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
    owner  => $httpd_user,
    group  => $httpd_user,
    mode    => '0640',
    content => template('cauth/cauth-config.py.erb'),
    require => File['/var/www/cauth/'],
    replace => true,
  }

  file { '/var/www/cauth/cauth/templates':
    ensure  => directory,
    owner   => $httpd_user,
    group   => $httpd_user,
    mode    => '0750',
    require => File['/var/www/cauth/'],
  }

  file {'/var/www/cauth/cauth/templates/login.html':
    ensure => file,
    mode   => '0640',
    owner  => $httpd_user,
    group  => $httpd_user,
    content => template('cauth/login.html'),
    require => File['/var/www/cauth/cauth/templates'],
  }
}
