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

class cauth_client () {
  file { '/srv/cauth_keys':
    ensure => directory,
    mode   => '0544',
    owner  => 'root',
    group  => 'root',
  }

  file { '/srv/cauth_keys/pubkey.pem':
    ensure => file,
    mode   => '0544',
    owner  => 'root',
    group  => 'root',
    require => File['/srv/cauth_keys'],
    source  => 'puppet:///modules/cauth/pubkey.pem'
  }

  file { '/etc/apache2/mods-available/auth_pubtkt.conf':
    ensure => file,
    mode   => '0544',
    owner  => 'root',
    group  => 'root',
    require => File['/srv/cauth_keys/pubkey.pem'],
    source  => 'puppet:///modules/cauth_client/auth_pubtkt.conf',
    replace => true
  }

  file { '/etc/apache2/mods-available/auth_pubtkt.load':
    ensure => present,
    mode   => '0544',
    owner  => 'root',
    group  => 'root',
  }

  exec { 'enable_mod_auth_pubtkt':
    command => 'a2enmod auth_pubtkt',
    path    => '/usr/sbin/:/usr/bin/:/bin/',
    require => [File['/etc/apache2/mods-available/auth_pubtkt.conf'],
                File['/etc/apache2/mods-available/auth_pubtkt.load']],
    notify => Service[apache2],
  }
}
