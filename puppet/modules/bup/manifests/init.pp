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

class bup {

    exec {'bup_init':
        path    => '/usr/bin:/usr/sbin:/bin:/usr/local/bin:/usr/local/sbin',
        command => 'bup init',
        cwd => '/root',
        user => 'root',
        creates => '/root/.bup/HEAD',
    }
}

define bup::scripts($name, $backup_script, $restore_script) {

  include ::bup

  file { "/root/backup_${name}.sh":
    ensure  => present,
    owner   => 'root',
    group   => 'root',
    mode    => '0744',
    content => template($backup_script),
  }

  file { "/root/restore_${name}.sh":
    ensure  => present,
    owner   => 'root',
    group   => 'root',
    mode    => '0744',
    content => template($restore_script),
  }
}
