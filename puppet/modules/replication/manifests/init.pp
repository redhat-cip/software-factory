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

class replication ($gerrit = hiera_hash('gerrit', '')) {

#To host gerrit config project as a mirror repo
  user { 'gerrit':
    ensure => present,
    home => '/home/gerrit',
    system => true,
    managehome => true,
    comment => 'Gerrit sys user',
    require => Group['gerrit']
  }
  group { 'gerrit':
    ensure => present,
  }
  file { '/home/gerrit/.ssh':
    ensure  => directory,
    owner   => 'gerrit',
    require => [User['gerrit'], Group['gerrit']],
  }
  ssh_authorized_key { 'gerrit_local_user':
    user => 'gerrit',
    type => 'rsa',
    key  => $gerrit['gerrit_local_key'],
    require => File['/home/gerrit/.ssh'],
  }
}
