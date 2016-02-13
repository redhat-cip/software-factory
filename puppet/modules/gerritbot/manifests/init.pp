# Copyright (c) 2016 Red Hat, Inc.
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

class gerritbot {

  $gerritbot = hiera('gerritbot')
  $gerritbot_rsa = hiera('jenkins_rsa')

  group { 'gerritbot':
    ensure => present,
  }

  user { 'gerritbot':
    ensure     => present,
    home       => '/var/lib/gerritbot',
    shell      => '/sbin/nologin',
    gid        => 'gerritbot',
    managehome => true,
    require    => Group['gerritbot'],
  }

  file { '/var/lib/gerritbot/.ssh':
    require    => User['gerritbot'],
    ensure     => directory,
    owner      => 'gerritbot',
    group      => 'gerritbot',
    mode       => '0700',
  }

  file { '/var/lib/gerritbot/.ssh/id_rsa':
    require => File['/var/lib/gerritbot/.ssh'],
    ensure  => file,
    owner   => 'gerritbot',
    group   => 'gerritbot',
    mode    => '0400',
    content => inline_template('<%= @gerritbot_rsa %>'),
  }

  file { '/var/log/gerritbot':
    ensure  => directory,
    owner   => 'gerritbot',
    group   => 'gerritbot',
  }

  file { '/etc/gerritbot':
    ensure  => directory,
  }

  file { '/etc/gerritbot/gerritbot.conf':
    require => File['/etc/gerritbot'],
    ensure  => file,
    mode    => '0600',
    content => template('gerritbot/gerritbot.conf.erb'),
  }

  file { '/etc/gerritbot/logging.conf':
    require => File['/etc/gerritbot'],
    ensure  => file,
    source  => 'puppet:///modules/gerritbot/logging.conf',
  }

  file { '/etc/gerritbot/channels.yaml':
    require => File['/etc/gerritbot'],
    ensure  => file,
    source  => 'puppet:///modules/gerritbot/channels.yaml',
    replace => false,
  }

  file { 'gerritbot_service':
    path    => '/lib/systemd/system/gerritbot.service',
    source  => 'puppet:///modules/gerritbot/gerritbot.service',
  }

  if $gerritbot['disabled'] {
    $running = false
    $enabled = false
  }
  else {
    $running = true
    $enabled = true
  }

  service { 'gerritbot':
    ensure     => $running,
    enable     => $enabled,
    hasrestart => true,
    require    => File['/lib/systemd/system/gerritbot.service'],
    subscribe  => [File['/etc/gerritbot/gerritbot.conf'],
                   File['/etc/gerritbot/channels.yaml'],
                   File['/etc/gerritbot/logging.conf']],
  }
}
