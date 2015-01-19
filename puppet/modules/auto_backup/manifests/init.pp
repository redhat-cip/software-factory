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

class auto_backup ($backup = hiera_hash('auto_backup', '')) {

  $m = hiera('admin_mail')

  file {'/etc/auto_backup.conf':
    ensure => file,
    mode   => '0640',
    content => template('auto_backup/auto_backup.conf.erb'),
  }

 file {'/root/puppet-bootstrapper/tools/backup_export/export_backup_swift.sh':
    ensure => file,
    mode   => '740',
  }

  cron {'auto_backup':
    command => "/root/puppet-bootstrapper/tools/backup_export/export_backup_swift.sh",
    environment => "MAILTO=$m",
    user    => root,
    hour    => 0,
    minute  => 30,
  }
}
