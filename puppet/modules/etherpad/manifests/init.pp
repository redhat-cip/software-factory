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

class etherpad {

  require hosts

  $session_key = hiera('creds_etherpad_session_key')
  $mysql_db_address = hiera('mysql_url')
  $mysql_db_secret = hiera('creds_etherpad_sql_pwd')
  $mysql_db_username = "etherpad"
  $mysql_db = "etherpad"

  file { 'init_script':
    path    => '/lib/systemd/system/etherpad.service',
    ensure  => present,
    mode    => '0740',
    source  => 'puppet:///modules/etherpad/etherpad.service',
    notify  => Exec["reload_unit"],
  }

  user { 'etherpad':
    name => 'etherpad',
    ensure => 'present',
    home => '/var/www/etherpad-lite',
    require => Group['etherpad'],
  }

  group { 'etherpad':
    ensure => present,
  }

  file { '/var/www/etherpad-lite':
    ensure  => directory,
    owner   => 'etherpad',
    group   => 'etherpad',
    require => [User['etherpad'],
                Group['etherpad']],
    notify  => Exec["change_owner"],
  }

  file { '/var/log/etherpad':
    ensure  => directory,
    owner   => 'etherpad',
    group   => 'etherpad',
    require => [User['etherpad'],
                Group['etherpad']],
  }

  file { '/var/www/etherpad-lite/run.sh':
    ensure  => present,
    owner   => 'etherpad',
    group   => 'etherpad',
    mode    => '0740',
    source  => 'puppet:///modules/etherpad/run.sh',
    require => File['/var/www/etherpad-lite'],
    notify  => Exec["change_owner"],
  }


  file { '/var/www/etherpad-lite/settings.json':
    ensure   => present,
    owner    => 'etherpad',
    group    => 'etherpad',
    mode     => '0640',
    content  => template('etherpad/settings.json.erb'),
    require  => File['/var/www/etherpad-lite'],
    notify   => [Service["etherpad"], Exec["change_owner"]],
  }

  exec {'change_owner':
    command => 'chown -R etherpad:etherpad /var/www/etherpad-lite',
    path    => '/usr/sbin/:/usr/bin/:/bin/',
    require => [File['/var/www/etherpad-lite/run.sh'],
                File['init_script'],
                File['/var/www/etherpad-lite/settings.json']],
    refreshonly => true,
  }

  exec {'reload_unit':
    command => 'systemctl daemon-reload',
    path    => '/usr/sbin/:/usr/bin/:/bin/',
    require => File['/lib/systemd/system/etherpad.service'],
    refreshonly => true,
  }

  service { "etherpad":
    ensure     => running,
    enable     => true,
    hasrestart => true,
    hasstatus  => true,
    require    => [File['/var/log/etherpad'],
                   Exec['change_owner']],
  }

  file { '/var/www/etherpad-lite/src/static/custom/pad.css':
    ensure  => present,
    owner   => 'etherpad',
    group   => 'etherpad',
    mode    => '0740',
    source  => 'puppet:///modules/etherpad/pad.css',
    require => File['/var/www/etherpad-lite'],
  }

}
