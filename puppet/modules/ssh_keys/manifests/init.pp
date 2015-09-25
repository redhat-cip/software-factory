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

class ssh_keys {

  $service_rsa = hiera('service_rsa')
  $keys = hiera_hash('ssh_keys', '')

  file { '/root/.ssh':
    ensure  => directory,
    owner   => 'root',
    group   => 'root',
    mode    => '0755',
  }

  create_resources('ssh_authorized_key', $keys)

  file { '/root/.ssh/id_rsa':
    ensure  => present,
    owner   => 'root',
    group   => 'root',
    mode    => '0600',
    content => inline_template('<%= @service_rsa %>'),
    require => File['/root/.ssh'],
  }
}
