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

class cauth ($gerrit = hiera('gerrit')) {
  include ::apache

  $auth = hiera('authentication')
  $fqdn = hiera('fqdn')
  $theme = hiera('theme')
  $url = hiera('url')
  $network = hiera('network')
  $admin_password = $auth['admin_password']
  $ldap = $auth['ldap']
  $github = $auth['oauth2']['github']
  $google = $auth['oauth2']['google']
  $bitbucket = $auth['oauth2']['bitbucket']
  $openid = $auth['openid']
  $issues_tracker_api_key = hiera('creds_issues_tracker_api_key')
  $gerrit_mysql_host = "mysql.${fqdn}"
  $gerrit_mysql_db = 'gerrit'
  $gerrit_mysql_username = 'gerrit'
  $cauth_mysql_host = "mysql.${fqdn}"
  $cauth_mysql_db = 'cauth'
  $cauth_mysql_username = 'cauth'
  $cauth_mysql_password = hiera('creds_cauth_sql_pwd')
  $gerrit_mysql_password = hiera('creds_gerrit_sql_pwd')
  $service_user_password = hiera('creds_sf_service_user_pwd')

  $admin_password_hashed = generate("/usr/bin/python", "-c", "import crypt, random, string, sys; salt = '\$6\$' + ''.join(random.choice(string.letters + string.digits) for _ in range(16)) + '\$'; sys.stdout.write(crypt.crypt(sys.argv[1], salt))", $auth['admin_password'])
  $service_user_password_hashed = generate("/usr/bin/python", "-c", "import crypt, random, string, sys; salt = '\$6\$' + ''.join(random.choice(string.letters + string.digits) for _ in range(16)) + '\$'; sys.stdout.write(crypt.crypt(sys.argv[1], salt))", $service_user_password)

  file {'/etc/httpd/conf.d/cauth.conf':
    ensure => file,
    mode   => '0640',
    owner  => 'apache',
    group  => 'apache',
    source => 'puppet:///modules/cauth/cauth.site',
    notify => Service['webserver'],
  }

  file { '/var/www/cauth/cauth/':
    ensure  => directory,
    owner   => 'apache',
    group   => 'apache',
    mode    => '0640',
  }

  file { '/var/lib/cauth/':
    ensure => directory,
    owner  => 'apache',
    group  => 'apache',
    mode   => '0750',
  }

  file { '/var/www/cauth/keys':
    ensure  => directory,
    owner   => 'root',
    group   => 'root',
    mode    => '0655',
  }

  file { '/var/log/cauth/':
    ensure => directory,
    owner  => 'apache',
    group  => 'apache',
    mode   => '0750',
  }

  file { '/var/www/cauth/config.py':
    ensure  => file,
    owner   => 'apache',
    group   => 'apache',
    mode    => '0640',
    content => template('cauth/cauth-config.py.erb'),
    replace => true,
    notify  => Service['webserver'],
  }

  file { '/var/www/cauth/cauth/templates':
    ensure  => directory,
    owner   => 'apache',
    group   => 'apache',
    mode    => '0750',
    require => File['/var/www/cauth/cauth/'],
  }

  file {'/var/www/cauth/cauth/templates/login.html':
    ensure  => file,
    mode    => '0640',
    owner   => 'apache',
    group   => 'apache',
    content => template('cauth/login.html.erb'),
    require => File['/var/www/cauth/cauth/templates'],
  }
}
