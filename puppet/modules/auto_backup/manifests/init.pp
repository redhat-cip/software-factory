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

class auto_backup {

  $fqdn = hiera('fqdn')
  $auth = hiera('authentication')
  $backup = hiera('backup')

  $mail = "admin@${fqdn}"
  $admin_password = $auth['admin_password']
  $os_auth_url = $backup['os_auth_url']
  $os_auth_version = $backup['os_auth_version']
  $os_tenant_name = $backup['os_tenant_name']
  $os_username = $backup['os_username']
  $os_password = $backup['os_password']

  file {'/etc/auto_backup.conf':
    ensure  => file,
    mode    => '0640',
    content => template('auto_backup/auto_backup.conf.erb'),
  }

  file {'/usr/local/bin/export_backup_swift.sh':
    ensure => file,
    mode   => '0740',
    source => 'puppet:///modules/auto_backup/export_backup_swift.sh',
  }

  cron {'auto_backup':
    command     => '/usr/local/bin/export_backup_swift.sh',
    environment => "MAILTO=${mail}",
    user        => root,
    hour        => 5,
    minute      => 0,
  }
}
