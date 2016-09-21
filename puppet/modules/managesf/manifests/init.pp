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

class managesf ($gerrit = hiera('gerrit')) {
  include ::apache

  $fqdn = hiera('fqdn')
  $url = hiera('url')
  $auth = hiera('authentication')
  $arch = hiera('roles')
  $issues_tracker_api_key = hiera('creds_issues_tracker_api_key')
  $storyboard_service_token = hiera('creds_storyboard_service_token')
  $storyboard_mysql_host = "mysql.${fqdn}"
  $storyboard_mysql_db = 'storyboard'
  $storyboard_mysql_username = 'storyboard'
  $storyboard_mysql_password = hiera('creds_storyboard_sql_pwd')

  $issues_tracker_api_url = $url["api_redmine_url"]
  $gerrit_host = "gerrit.${fqdn}"
  $gerrit_admin_rsa = hiera('gerrit_admin_rsa')
  $gerrit_admin_sshkey_rsa = hiera('creds_gerrit_admin_sshkey')
  $gerrit_admin_sshkey = "ssh-rsa ${gerrit_admin_sshkey_rsa}"
  $service_rsa = hiera('service_rsa')
  $gerrit_mysql_host = "mysql.${fqdn}"
  $gerrit_mysql_db = 'gerrit'
  $gerrit_mysql_username = 'gerrit'
  $gerrit_mysql_password = hiera('creds_gerrit_sql_pwd')
  $admin_password = $auth['admin_password']
  $admin_mail_forward = $auth['admin_mail_forward']
  $managesf_mysql_host = "mysql.${fqdn}"
  $managesf_mysql_db = 'managesf'
  $managesf_mysql_username = 'managesf'
  $managesf_mysql_password = hiera('creds_managesf_sql_pwd')
  $redmine_mysql_host = "mysql.${fqdn}"
  $redmine_mysql_db = 'redmine'

  file {'/etc/httpd/conf.d/managesf.conf':
    ensure  => file,
    mode    => '0640',
    owner   => 'apache',
    group   => 'apache',
    content => template('managesf/managesf.site.erb'),
    notify  => Service['webserver'],
  }

# managesf can't access keys in /root/.ssh and can only
# access keys from /var/www/.ssh, so creating keys here
  file { '/usr/share/httpd/.ssh':
    ensure => directory,
    owner  => 'apache',
    group  => 'apache',
    mode   => '0755',
  }

  file { '/usr/share/httpd/.ssh/id_rsa':
    ensure  => file,
    owner   => 'apache',
    group   => 'apache',
    mode    => '0600',
    content => inline_template('<%= @service_rsa %>'),
    require => File['/usr/share/httpd/.ssh'],
  }

  file { '/var/log/managesf/':
    ensure => directory,
    owner  => 'apache',
    group  => 'apache',
    mode   => '0750',
  }

  file { '/var/lib/managesf/':
    ensure => directory,
    owner  => 'apache',
    group  => 'apache',
    mode   => '0750',
  }

  file { '/var/www/managesf/':
    ensure => directory,
    owner  => 'apache',
    group  => 'apache',
    mode   => '0640',
  }

  file { '/var/www/managesf/config.py':
    ensure  => file,
    owner   => 'apache',
    group   => 'apache',
    mode    => '0640',
    content => template('managesf/managesf-config.py.erb'),
    require => File['/var/www/managesf/'],
    replace => true,
  }

  file { '/var/www/managesf/gerrit_admin_rsa':
    ensure  => file,
    owner   => 'apache',
    group   => 'apache',
    mode    => '0400',
    content => inline_template('<%= @gerrit_admin_rsa %>'),
    require => File['/var/www/managesf/'],
  }

  file { '/var/www/managesf/sshconfig':
    ensure  => directory,
    owner   => 'apache',
    group   => 'apache',
    mode    => '0640',
    require => File['/var/www/managesf/'],
  }

  file {'/root/sf-bootstrap-data/ssh_keys/gerrit_admin_rsa':
    ensure  => file,
    mode    => '0400',
    owner   => 'root',
    group   => 'root',
    content => inline_template('<%= @gerrit_admin_rsa %>'),
  }

  file {'/root/sf-bootstrap-data/ssh_keys/gerrit_admin_rsa.pub':
    ensure  => file,
    mode    => '0400',
    owner   => 'root',
    group   => 'root',
    content => inline_template('<%= @gerrit_admin_sshkey %>'),
  }
}
