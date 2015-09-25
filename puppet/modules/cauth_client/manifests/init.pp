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
  include apache

  $pubkey_pem = hiera('pubkey_pem')

  file { '/etc/httpd/conf.modules.d/00-tkt.conf':
    ensure => present,
    content => "LoadModule auth_pubtkt_module modules/mod_auth_pubtkt.so",
    mode   => '0544',
    owner  => 'root',
    group  => 'root',
    notify => Service['webserver'],
  }

  file { 'auth_pubtkt_conf':
    path   => "/etc/httpd/conf.d/auth_pubtkt.conf",
    ensure => file,
    mode   => '0544',
    owner  => 'root',
    group  => 'root',
    require => File['/srv/cauth_keys/pubkey.pem'],
    content => "TKTAuthPublicKey /srv/cauth_keys/pubkey.pem",
    notify => Service['webserver'],
    replace => true
  }

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
    content => inline_template('<%= @pubkey_pem %>'),
  }

}
