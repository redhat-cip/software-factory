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

class commonservices-apache ($cauth = hiera_hash('cauth', '')) {
  require hosts
  include apache

  $auth = hiera('authentication')
  $url = hiera('url')
  $authenticated_only = $auth['authenticated_only']
  $gateway_crt = hiera('gateway_crt')
  $gateway_key = hiera('gateway_key')
  $network = hiera('network')
  $fqdn = hiera('fqdn')
  $theme = hiera('theme')
  $sf_version = hiera('sf_version')

  file {'gateway_crt':
    path  => '/etc/httpd/conf.d/gateway.crt',
    content => inline_template('<%= @gateway_crt %>'),
    ensure => file,
    mode   => '0640',
    owner  => $httpd_user,
    group  => $httpd_user,
  }

  file {'gateway_key':
    path  => '/etc/httpd/conf.d/gateway.key',
    content => inline_template('<%= @gateway_key %>'),
    ensure => file,
    mode   => '0640',
    owner  => $httpd_user,
    group  => $httpd_user,
  }

  file {'gateway_common':
    path   => '/etc/httpd/conf.d/gateway.common',
    ensure => file,
    mode   => '0640',
    owner  => $httpd_user,
    group  => $httpd_user,
    content => template('commonservices-apache/gateway.common'),
  }

  file {'gateway_conf':
    path   => '/etc/httpd/conf.d/gateway.conf',
    ensure => file,
    mode   => '0640',
    owner  => $httpd_user,
    group  => $httpd_user,
    content => template('commonservices-apache/gateway.conf'),
    notify => Service['webserver'],
    require => [File['gateway_crt'],
                File['gateway_key'],
                File['gateway_common'],
                File['ssl.conf'],
                File['00-ssl.conf']]
  }

  file {'/var/www/static/js/topmenu.js':
    ensure => file,
    mode   => '0640',
    owner  => $httpd_user,
    group  => $httpd_user,
    content => template('commonservices-apache/topmenu.js'),
  }

  file {'/var/www/static/js/menu.js':
    ensure => file,
    mode   => '0640',
    owner  => $httpd_user,
    group  => $httpd_user,
    source  => 'puppet:///modules/commonservices-apache/menu.js',
  }

  file {'/var/www/topmenu.html':
    ensure => file,
    mode   => '0640',
    owner  => $httpd_user,
    group  => $httpd_user,
    content => template('commonservices-apache/topmenu.html'),
  }

  file {'/var/www/dashboard':
    ensure => directory,
    recurse => true,
    mode   => '0644',
    owner  => $httpd_user,
    group  => $httpd_user,
  }

  file {'/var/www/dashboard/index.html':
    ensure => file,
    mode   => '0640',
    owner  => $httpd_user,
    group  => $httpd_user,
    source => 'puppet:///modules/commonservices-apache/dashboard.html',
    require => File['/var/www/dashboard'],
  }

   file {'/var/www/dashboard/dashboard.js':
    ensure => file,
    mode   => '0640',
    owner  => $httpd_user,
    group  => $httpd_user,
    source => 'puppet:///modules/commonservices-apache/dashboard.js',
    require => File['/var/www/dashboard'],
  }

  file {'managesf_htpasswd':
    path   => '/etc/httpd/managesf_htpasswd',
    ensure => file,
    mode   => '0640',
    owner  => $httpd_user,
    group  => $httpd_user,
  }
}
