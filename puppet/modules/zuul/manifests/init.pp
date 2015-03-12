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

class zuul ($settings = hiera_hash('jenkins', ''), $gh = hiera('gerrit_host'), $hosts = hiera('hosts')){

  require hosts

  $gfqdn = "$gh"
  $gip = $hosts[$gfqdn]['ip']

  $http = "httpd"
  $provider = "systemd"
  $httpd_user = "apache"
  $pub_html_path = "/var/www/zuul"
  $gitweb_path = "/usr/libexec/git-core"

  file { '/var/www/zuul':
    ensure  => link,
    target  => '/srv/zuul/etc/status/public_html',
  }

  file {'/srv/zuul/etc/status/public_html/index.html':
    ensure  => present,
    mode    => '0644',
    source  => 'puppet:///modules/zuul/index.html',
  }

  file {'/etc/httpd/conf.d/zuul.conf':
    ensure => file,
    mode   => '0640',
    owner  => $httpd_user,
    group  => $httpd_user,
    content => template('zuul/zuul.site.erb'),
    notify => Service['webserver'],
  }

  file {'zuul_init':
    path   => '/lib/systemd/system/zuul.service',
    ensure => present,
    mode   => '0555',
    owner  => 'root',
    group  => 'root',
    source => 'puppet:///modules/zuul/zuul.systemd.service'
  }

  file {'zuul_merger_init':
    path   => '/lib/systemd/system/zuul-merger.service',
    ensure => present,
    mode   => '0555',
    group  => 'root',
    owner  => 'root',
    source => 'puppet:///modules/zuul/zuul-merger.systemd.service'
  }

  group { 'zuul':
    ensure => present,
  }

  user { 'zuul':
    ensure     => present,
    home       => '/home/zuul',
    shell      => '/bin/bash',
    gid        => 'zuul',
    managehome => true,
    require    => Group['zuul'],
  }

  file {'/home/zuul/.ssh':
    ensure  => directory,
    mode    => '0777',
    owner   => 'zuul',
    group   => 'zuul',
    require => [User['zuul'], Group['zuul']],
  }

  exec {'update_gerritip_knownhost':
    command => "/usr/bin/ssh-keyscan -p 29418 $gip >> /home/zuul/.ssh/known_hosts",
    logoutput => true,
    user => 'zuul',
    require => File['/home/zuul/.ssh'],
    unless => '/usr/bin/grep "$gip" /home/zuul/.ssh/known_hosts',
  }

  exec {'update_gerrithost_knownhost':
    command => "/usr/bin/ssh-keyscan -p 29418 $gh >> /home/zuul/.ssh/known_hosts",
    logoutput => true,
    user => 'zuul',
    require => File['/home/zuul/.ssh'],
    unless => '/usr/bin/grep "$gh" /home/zuul/.ssh/known_hosts',
  }

  file {'/usr/share/sf-zuul':
    ensure  => directory,
    mode    => '0640',
    owner   => 'root',
    group   => 'root',
  }

  file {'/usr/share/sf-zuul/layout.yaml':
    ensure => file,
    mode   => '0640',
    owner  => "root",
    group  => "root",
    require => File['/usr/share/sf-zuul'],
    content => template('zuul/layout.yaml.erb'),
  }

  file {'/usr/share/sf-zuul/projects.yaml':
    ensure => file,
    mode   => '0640',
    owner  => "root",
    group  => "root",
    require => File['/usr/share/sf-zuul'],
    content => template('zuul/projects.yaml.erb'),
  }

  file {'/var/log/zuul/':
    ensure  => directory,
    mode    => '0755',
    owner   => 'zuul',
    group   => 'zuul',
    require => [User['zuul'], Group['zuul']],
  }

  file {'/etc/zuul':
    ensure  => directory,
    mode    => '0750',
    owner   => 'zuul',
    group   => 'zuul',
    require => [User['zuul'], Group['zuul']],
  }

  file {'/var/lib/zuul/':
    ensure  => directory,
    mode    => '0755',
    owner   => 'zuul',
    group   => 'zuul',
    require => [User['zuul'], Group['zuul']],
  }

  file {'/var/lib/zuul/.ssh':
    ensure  => directory,
    mode    => '0755',
    owner   => 'zuul',
    group   => 'zuul',
    require => File['/var/lib/zuul/'],
  }

  file {'/var/lib/zuul/.ssh/id_rsa':
    ensure  => present,
    mode    => '0400',
    owner   => 'zuul',
    group   => 'zuul',
    source  => 'puppet:///modules/zuul/jenkins_rsa',
    require => File['/var/lib/zuul/.ssh'],
  }

  file {'/var/run/zuul/':
    ensure  => directory,
    mode    => '0755',
    owner   => 'zuul',
    group   => 'zuul',
    require => [User['zuul'], Group['zuul']],
  }

  file {'/etc/zuul/logging.conf':
    ensure  => file,
    mode    => '0644',
    owner   => 'zuul',
    group   => 'zuul',
    source  => 'puppet:///modules/zuul/logging.conf',
    require => File['/etc/zuul'],
  }

  file {'/etc/zuul/gearman-logging.conf':
    ensure  => file,
    mode    => '0644',
    owner   => 'zuul',
    group   => 'zuul',
    source  => 'puppet:///modules/zuul/gearman-logging.conf',
    require => File['/etc/zuul'],
  }

  file {'/etc/zuul/merger-logging.conf':
    ensure  => file,
    mode    => '0644',
    owner   => 'zuul',
    group   => 'zuul',
    source  => 'puppet:///modules/zuul/merger-logging.conf',
    require => File['/etc/zuul'],
  }

  file {'/etc/zuul/zuul.conf':
    ensure  => file,
    mode    => '0644',
    owner   => 'zuul',
    group   => 'zuul',
    content => template('zuul/zuul.conf.erb'),
    require => [File['/etc/zuul/logging.conf'],
                File['/etc/zuul/gearman-logging.conf'],
                File['/etc/zuul/merger-logging.conf']],
  }

  file {'/etc/zuul/layout.yaml':
    ensure  => file,
    mode    => '0644',
    owner   => 'zuul',
    group   => 'zuul',
    require => [File['/etc/zuul']],
  }

  service {'zuul':
    ensure  => running,
    enable  => 'true',
    require => [File['/lib/systemd/system/zuul.service'],
                File['/etc/zuul/zuul.conf'],
                File['/etc/zuul/layout.yaml'],
                File['/var/log/zuul/'],
                File['/var/run/zuul/']]
  }

  service {'zuul-merger':
    ensure  => running,
    enable  => 'true',
    require => [File['/lib/systemd/system/zuul-merger.service'],
                File['/var/lib/zuul'],
                Service['zuul'],
                Exec['update_gerritip_knownhost'],
                Exec['update_gerrithost_knownhost']],
  }
}
