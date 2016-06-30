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

class lodgeit {
  include ::systemctl

  $fqdn = hiera('fqdn')
  $session_key = hiera('creds_lodgeit_session_key')
  $mysql_db_address = "mysql.${fqdn}"
  $mysql_db_secret = hiera('creds_lodgeit_sql_pwd')
  $mysql_db_username = 'lodgeit'
  $mysql_db = 'lodgeit'

  file {'init':
    ensure  => file,
    path    => '/lib/systemd/system/lodgeit.service',
    mode    => '0755',
    source  => 'puppet:///modules/lodgeit/lodgeit.service',
    require => File['/srv/lodgeit/lodgeit/manage.py'],
    notify  => Exec['systemctl_reload'],
  }

  file { '/srv/lodgeit/lodgeit/manage.py':
    ensure  => file,
    mode    => '0755',
    replace => true,
    owner   => 'apache',
    group   => 'apache',
    content => template('lodgeit/manage.py.erb'),
    notify  => Service['lodgeit'],
  }

  file { '/srv/lodgeit/lodgeit/lodgeit/urls.py':
    ensure  => file,
    mode    => '0755',
    replace => true,
    owner   => 'apache',
    group   => 'apache',
    source  => 'puppet:///modules/lodgeit/urls.py',
    notify  => Service['lodgeit'],
  }

  service {'lodgeit':
    ensure    => running,
    enable    => true,
    hasstatus => true,
    require   => [File['init'],
        File['wait4mariadb'],
        Exec['systemctl_reload'],
        File['/srv/lodgeit/lodgeit/manage.py'],
        File['/srv/lodgeit/lodgeit/lodgeit/urls.py']],
  }

  file { '/var/www/static/lodgeit':
    ensure => link,
    target => '/srv/lodgeit/lodgeit/lodgeit/static/',
  }

  bup::scripts{ 'lodgeit_scripts':
    name           => 'lodgeit',
    backup_script  => 'lodgeit/backup.sh.erb',
    restore_script => 'lodgeit/restore.sh.erb',
  }
}
