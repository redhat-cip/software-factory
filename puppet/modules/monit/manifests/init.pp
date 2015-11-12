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

class monit {

  require hosts

  $fqdn = hiera('fqdn')
  $mail_from = "monit@${fqdn}"
  # mail forward managed by admin_mail_forward parameter
  $mail_to = 'root@localhost'
  $provider = 'systemd'

  package { 'monit':
    ensure => present,
  }

  file { '/etc/monit':
    ensure  => directory,
    require => Package['monit'],
  }

  file { '/etc/monit.d':
    ensure  => directory,
    require => Package['monit'],
  }
  file { '/etc/monitrc':
    ensure  => file,
    mode    => '0600',
    content => template('monit/monitrc.erb'),
    require => [Package['monit'], File['/etc/monit']],
    replace => true,
  }

  service { 'monit':
    ensure     => running,
    enable     => true,
    hasrestart => true,
    provider   => $provider,
    require    => Package['monit'],
    subscribe  => File['/etc/monitrc'],
  }

  file { '/etc/monit.d/rootfs':
    ensure  => file,
    source  => 'puppet:///modules/monit/rootfs',
    require => [Package['monit'], File['/etc/monit.d']],
    notify  => Service['monit'],
  }

  file { '/etc/monit.d/system':
    ensure  => file,
    source  => 'puppet:///modules/monit/system',
    require => [Package['monit'], File['/etc/monit.d']],
    notify  => Service['monit'],
  }

}
