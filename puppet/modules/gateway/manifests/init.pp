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

class gateway {
  include ::apache

  $cauth_signin_url = "/auth/login"
  $cauth_signout_url = "/auth/logout"
  $auth = hiera('authentication')
  $arch = hiera('roles')
  $url = hiera('url')
  $murmur = hiera('mumble')
  $authenticated_only = $auth['authenticated_only']
  $allowed_proxy_prefixes = $auth['allowed_proxy_prefixes']
  $gateway_crt = hiera('gateway_crt')
  $gateway_key = hiera('gateway_key')
  $gateway_chain = hiera('gateway_chain')
  $network = hiera('network')
  $fqdn = hiera('fqdn')
  $theme = hiera('theme')
  $sf_version = hiera('sf_version')

  if $network['use_letsencrypt'] {
    file {'gateway_crt':
      ensure  => symlink,
      path    => '/etc/httpd/conf.d/gateway.crt',
      target  => "/etc/letsencrypt/pem/${fqdn}.pem",
    }

    file {'gateway_chain':
      ensure  => symlink,
      path    => '/etc/httpd/conf.d/gateway-chain.crt',
      target  => '/etc/letsencrypt/pem/lets-encrypt-x3-cross-signed.pem',
    }

    file {'gateway_key':
      ensure  => symlink,
      path    => '/etc/httpd/conf.d/gateway.key',
      target  => "/etc/letsencrypt/private/${fqdn}.key",
    }
  } else {
    file {'gateway_crt':
      ensure  => file,
      path    => '/etc/httpd/conf.d/gateway.crt',
      content => inline_template('<%= @gateway_crt %>'),
      mode    => '0640',
      owner   => 'apache',
      group   => 'apache',
    }

    file {'gateway_chain':
      ensure  => file,
      path    => '/etc/httpd/conf.d/gateway-chain.crt',
      content => inline_template('<%= @gateway_chain %>'),
      mode    => '0640',
      owner   => 'apache',
      group   => 'apache',
    }

    file {'gateway_key':
      ensure  => file,
      path    => '/etc/httpd/conf.d/gateway.key',
      content => inline_template('<%= @gateway_key %>'),
      mode    => '0640',
      owner   => 'apache',
      group   => 'apache',
    }
  }

  exec { 'reload_httpd_cert':
    command => '/usr/bin/systemctl reload httpd',
    subscribe => [File['gateway_crt'],
                  File['gateway_chain'],
                  File['gateway_key']]
  }

  file {'gateway_common':
    ensure  => file,
    path    => '/etc/httpd/conf.d/gateway.common',
    mode    => '0640',
    owner   => 'apache',
    group   => 'apache',
    content => template('gateway/gateway.common.erb'),
  }

  file {'pages':
    ensure  => file,
    path    => '/etc/httpd/pages.txt',
    mode    => '0640',
    owner   => 'apache',
    group   => 'apache',
    content => "",
    replace => false,
  }

  file {'gateway_conf':
    ensure  => file,
    path    => '/etc/httpd/conf.d/gateway.conf',
    mode    => '0640',
    owner   => 'apache',
    group   => 'apache',
    content => template('gateway/gateway.conf.erb'),
    notify  => Service['webserver'],
    require => [File['gateway_crt'],
                File['gateway_key'],
                File['gateway_common']]
  }

  file {'/var/www/static/js/topmenu.js':
    ensure  => file,
    mode    => '0640',
    owner   => 'apache',
    group   => 'apache',
    content => template('gateway/topmenu.js.erb'),
  }

  file {'/var/www/static/js/menu.js':
    ensure => file,
    mode   => '0640',
    owner  => 'apache',
    group  => 'apache',
    source => 'puppet:///modules/gateway/menu.js',
  }

  file {'/var/www/static/js/hideci.js':
    ensure => file,
    mode   => '0640',
    owner  => 'apache',
    group  => 'apache',
    content => template('gateway/hideci.js.erb'),
  }

  file {'/var/www/topmenu.html':
    ensure  => file,
    mode    => '0640',
    owner   => 'apache',
    group   => 'apache',
    content => template('gateway/topmenu.html.erb'),
  }

  file {'/var/www/dashboard':
    ensure  => directory,
    recurse => true,
    mode    => '0644',
    owner   => 'apache',
    group   => 'apache',
  }

  file {'/var/www/dashboard/index.html':
    ensure  => file,
    mode    => '0640',
    owner   => 'apache',
    group   => 'apache',
    source  => 'puppet:///modules/gateway/dashboard.html',
    require => File['/var/www/dashboard'],
  }

  file {'/var/www/dashboard/dashboard.js':
    ensure  => file,
    mode    => '0640',
    owner   => 'apache',
    group   => 'apache',
    source  => 'puppet:///modules/gateway/dashboard.js',
    require => File['/var/www/dashboard'],
  }

  file {'/var/www/pages-404.html':
    ensure  => file,
    mode    => '0640',
    owner   => 'apache',
    group   => 'apache',
    source  => 'puppet:///modules/gateway/pages-404.html',
  }

  file {'managesf_htpasswd':
    ensure => file,
    path   => '/etc/httpd/managesf_htpasswd',
    mode   => '0640',
    owner  => 'apache',
    group  => 'apache',
  }

  file {'base64helper':
    ensure  => file,
    path    => '/usr/local/sbin/base64helper',
    source  => 'puppet:///modules/gateway/base64helper',
    mode    => '0755',
    owner   => 'apache',
    group   => 'apache',
  }

  file {'/etc/httpd/conf.d/autoindex.conf':
    ensure  => absent,
  }

  file {'/etc/httpd/conf.d/userdir.conf':
    ensure  => absent,
  }

  file {'/etc/httpd/conf.d/welcome.conf':
    ensure  => absent,
  }
}
