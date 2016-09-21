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

class zuul {
  include ::apache
  include ::systemctl

  $arch = hiera('roles')
  $fqdn = hiera('fqdn')
  $logs = hiera('logs')
  $gerrit_host = "gerrit.${fqdn}"
  $gerrit_connections = hiera('gerrit_connections')

  $pub_html_path = '/var/www/zuul'
  $gitweb_path = '/usr/libexec/git-core'

  file {'/var/www/zuul/index.html':
    ensure => file,
    mode   => '0644',
    source => 'puppet:///modules/zuul/index.html',
  }

  file {'/etc/httpd/conf.d/zuul.conf':
    ensure  => file,
    mode    => '0640',
    owner   => 'apache',
    group   => 'apache',
    content => template('zuul/zuul.site.erb'),
    notify  => Service['webserver'],
  }

  file {'zuul_init':
    ensure => file,
    path   => '/lib/systemd/system/zuul.service',
    mode   => '0555',
    owner  => 'root',
    group  => 'root',
    source => 'puppet:///modules/zuul/zuul.service',
    notify  => Exec['systemctl_reload'],
  }

  file {'zuul_merger_init':
    ensure => file,
    path   => '/lib/systemd/system/zuul-merger.service',
    mode   => '0555',
    group  => 'root',
    owner  => 'root',
    source => 'puppet:///modules/zuul/zuul-merger.service',
    notify  => Exec['systemctl_reload'],
  }

  file {'/var/log/zuul/':
    ensure  => directory,
    mode    => '0755',
    owner   => 'zuul',
    group   => 'zuul',
  }

  file {'/etc/sysconfig/zuul':
    content => template('graphite/statsd.environment.erb'),
  }

  file {'/var/run/zuul/':
    ensure  => directory,
    mode    => '0755',
    owner   => 'zuul',
    group   => 'zuul',
  }

  file {'/etc/zuul/logging.conf':
    ensure  => file,
    mode    => '0644',
    owner   => 'zuul',
    group   => 'zuul',
    source  => 'puppet:///modules/zuul/logging.conf',
  }

  file {'/etc/zuul/gearman-logging.conf':
    ensure  => file,
    mode    => '0644',
    owner   => 'zuul',
    group   => 'zuul',
    source  => 'puppet:///modules/zuul/gearman-logging.conf',
  }

  file {'/etc/zuul/merger-logging.conf':
    ensure  => file,
    mode    => '0644',
    owner   => 'zuul',
    group   => 'zuul',
    source  => 'puppet:///modules/zuul/merger-logging.conf',
  }

  file {'/etc/zuul/layout.yaml':
    ensure  => file,
    mode    => '0644',
    owner   => 'zuul',
    group   => 'zuul',
  }

  file {'gearman-check':
    ensure => file,
    path   => '/usr/local/bin/gearman-check',
    mode   => '0755',
    owner  => 'root',
    group  => 'root',
    source => 'puppet:///modules/zuul/gearman-check',
  }

  cron {'gearman-check-cron':
    command => '/usr/local/bin/gearman-check',
    ensure  => present,
    user    => root,
    hour    => 0,
    minute  => 0,
    require => [File['gearman-check']],
  }
}
