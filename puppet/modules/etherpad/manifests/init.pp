#
# Copyright (C) 2016 Red Hat
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
  include ::systemctl

  $fqdn = hiera('fqdn')
  $admin_key = hiera('creds_etherpad_admin_key')
  $mysql_db_address = "mysql.${fqdn}"
  $mysql_db_secret = hiera('creds_etherpad_sql_pwd')
  $mysql_db_username = 'etherpad'
  $mysql_db = 'etherpad'

  file { 'init_script':
    ensure => file,
    path   => '/lib/systemd/system/etherpad.service',
    mode   => '0740',
    source => 'puppet:///modules/etherpad/etherpad.service',
    notify => Exec['systemctl_reload'],
    require => File['wait4mariadb'],
  }

  user { 'etherpad':
    ensure  => present,
    name    => 'etherpad',
    home    => '/var/www/etherpad-lite',
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
    notify  => Exec['change_owner'],
  }

  file { '/var/log/etherpad':
    ensure  => directory,
    owner   => 'etherpad',
    group   => 'etherpad',
    require => [User['etherpad'],
                Group['etherpad']],
  }

  file { '/var/www/etherpad-lite/run.sh':
    ensure  => file,
    owner   => 'etherpad',
    group   => 'etherpad',
    mode    => '0740',
    source  => 'puppet:///modules/etherpad/run.sh',
    require => File['/var/www/etherpad-lite'],
    notify  => Exec['change_owner'],
  }


  file { '/var/www/etherpad-lite/settings.json':
    ensure  => file,
    owner   => 'etherpad',
    group   => 'etherpad',
    mode    => '0640',
    content => template('etherpad/settings.json.erb'),
    require => File['/var/www/etherpad-lite'],
    notify  => [Service['etherpad'], Exec['change_owner']],
  }

  exec {'change_owner':
    command     => 'chown -R etherpad:etherpad /var/www/etherpad-lite',
    path        => '/usr/sbin/:/usr/bin/:/bin/',
    require     => [File['/var/www/etherpad-lite/run.sh'],
      File['init_script'],
      File['/var/www/etherpad-lite/settings.json']],
    refreshonly => true,
  }

  service { 'etherpad':
    ensure     => running,
    enable     => true,
    hasrestart => true,
    hasstatus  => true,
    require    => [File['/var/log/etherpad'],
                   Exec['systemctl_reload'],
                   Exec['change_owner'],
                   File['wait4mariadb']],
  }

  file { '/var/www/etherpad-lite/src/static/custom/pad.css':
    ensure  => file,
    owner   => 'etherpad',
    group   => 'etherpad',
    mode    => '0740',
    source  => 'puppet:///modules/etherpad/pad.css',
    require => File['/var/www/etherpad-lite'],
  }

  bup::scripts{ 'etherpad_scripts':
    name           => 'etherpad',
    backup_script  => 'etherpad/backup.sh.erb',
    restore_script => 'etherpad/restore.sh.erb',
  }
}
