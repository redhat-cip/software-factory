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

class managesf ($gerrit = hiera_hash('gerrit', ''),
                $redmine = hiera_hash('redmine', ''),
                $gerrit_host = hiera('gerrit_host'),
                $hosts = hiera('hosts'),
                $cauth = hiera_hash("cauth", '')) {

  require hosts

  $gerrit_ip = $hosts["$gerrit_host"]['ip']
  $gerrit_admin_rsa = hiera('gerrit_admin_rsa')
  $service_rsa = hiera('service_rsa')

  file {'/etc/httpd/conf.d/managesf.conf':
    ensure => file,
    mode   => '0640',
    owner  => $httpd_user,
    group  => $httpd_user,
    content=> template('managesf/managesf.site.erb'),
    notify => Service['webserver'],
  }

# managesf can't access keys in /root/.ssh and can only
# access keys from /var/www/.ssh, so creating keys here
  file { '/usr/share/httpd/.ssh':
    ensure  => directory,
    owner   => $httpd_user,
    group   => $httpd_user,
    mode    => '0755',
  }

  file { '/usr/share/httpd/.ssh/id_rsa':
    ensure  => present,
    owner   => $httpd_user,
    group   => $httpd_user,
    mode    => '0600',
    content => inline_template('<%= @service_rsa %>'),
    require => File['/usr/share/httpd/.ssh'],
  }

  file { '/var/log/managesf/':
    ensure  => directory,
    owner   => $httpd_user,
    group   => $httpd_user,
    mode    => '0750',
  }

  file { '/var/lib/managesf/':
    ensure  => directory,
    owner   => $httpd_user,
    group   => $httpd_user,
    mode    => '0750',
  }

  file { '/var/www/managesf/':
    ensure  => directory,
    owner   => $httpd_user,
    group   => $httpd_user,
    mode    => '0640',
  }

  file { '/var/www/managesf/config.py':
    ensure  => present,
    owner   => $httpd_user,
    group   => $httpd_user,
    mode    => '0640',
    content => template('managesf/managesf-config.py.erb'),
    require => File['/var/www/managesf/'],
    replace => true,
  }

  file { '/var/www/managesf/gerrit_admin_rsa':
    ensure => present,
    owner   => $httpd_user,
    group   => $httpd_user,
    mode   => '0400',
    content => inline_template('<%= @gerrit_admin_rsa %>'),
    require => File['/var/www/managesf/'],
  }

  exec {'update_gerritip_knownhost':
    command => "/usr/bin/ssh-keyscan $gerrit_ip >> /usr/share/httpd/.ssh/known_hosts",
    logoutput => true,
    user   => $httpd_user,
    require => File['/usr/share/httpd/.ssh'],
    unless => "/usr/bin/grep '$gerrit_ip ' /usr/share/httpd/.ssh/known_hosts",
  }

  exec {'update_gerrithost_knownhost':
    command => "/usr/bin/ssh-keyscan $gerrit_host >> /usr/share/httpd/.ssh/known_hosts",
    logoutput => true,
    user   => $httpd_user,
    require => File['/usr/share/httpd/.ssh'],
    unless => "/usr/bin/grep '$gerrit_host ' /usr/share/httpd/.ssh/known_hosts",
  }

  file { '/var/www/managesf/sshconfig':
    ensure  => directory,
    owner   => $httpd_user,
    group   => $httpd_user,
    mode    => '0640',
    require => File['/var/www/managesf/'],
  }

}
