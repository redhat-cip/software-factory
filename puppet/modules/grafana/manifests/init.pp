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

class grafana {
  include ::systemctl

  $fqdn = hiera('fqdn')
  $mysql_host = "mysql.${fqdn}"
  $mysql_port = 3306
  $mysql_user = 'grafana'
  $mysql_password = hiera('creds_grafana_sql_pwd')
  $mysql_db = 'grafana'

  file { '/etc/grafana/grafana.ini':
    ensure => file,
    mode   => '0755',
    owner  => 'root',
    group  => 'root',
    content => template('grafana/grafana.ini'),
  }

  file_line{ 'grafana-systemd-order':
    path  => '/usr/lib/systemd/system/grafana-server.service',
    line  => 'After=network-online.target mariadb.service',
    match => '^After=',
  }

  service { 'grafana-server':
    ensure     => true,
    enable     => true,
    hasrestart => true,
    require    => [File['/etc/grafana/grafana.ini'],
                   Exec['systemctl_reload']],
    subscribe   => File['/etc/grafana/grafana.ini'],
  }

  file { '/root/grafana-init.sql':
    ensure => file,
    mode   => '0755',
    owner  => 'root',
    group  => 'root',
    source => 'puppet:///modules/grafana/grafana-init.sql',
    notify  => Exec["grafana-init"],
  }

  exec { 'grafana-init':
    command     => "/usr/bin/mysql -u ${mysql_user} -p${mysql_password} -h ${mysql_host} ${mysql_db} < /root/grafana-init.sql",
    logoutput   => true,
    require     => [
        File['/root/grafana-init.sql'],
        Service['grafana-server']],
    refreshonly => true,
  }
}
