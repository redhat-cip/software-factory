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

class commonservices-apache {

  case $operatingsystem {
    centos: {
      $http = "httpd"
      $provider = "systemd"
      $gateway_conf = "/etc/httpd/conf.d/gateway.conf"
      $httpd_user = "apache"
    }

    debian: {
      $http = "apache2"
      $provider = "debian"
      $gateway_conf = "/etc/apache2/sites-available/gateway"
      $httpd_user = "www-data"

      exec {'enable_gateway':
        command => 'a2ensite gateway',
        path    => '/usr/sbin/:/usr/bin/:/bin/',
        require => File['gateway_conf'],
        before  => Class['monit'],
      }
    }
  }

  file {'gateway_conf':
    path   => $gateway_conf,
    ensure => file,
    mode   => '0640',
    owner  => $httpd_user,
    group  => $httpd_user,
    content => template('commonservices-apache/gateway'),
    notify => Service['webserver'],
  }

  file {'/var/www/index.py':
    ensure => file,
    mode   => '0740',
    owner  => $httpd_user,
    group  => $httpd_user,
    source  => 'puppet:///modules/commonservices-apache/index.py',
    notify => Service['webserver'],
  }

  file {'/var/www/index.html.tmpl':
    ensure => file,
    mode   => '0640',
    owner  => $httpd_user,
    group  => $httpd_user,
    source  => 'puppet:///modules/commonservices-apache/index.html.tmpl',
    notify => Service['webserver'],
  }

  file {'/var/www/docs':
    ensure => directory,
    recurse => true,
    mode   => '0644',
    owner  => $httpd_user,
    group  => $httpd_user,
  }

  file {'/var/www':
    ensure => directory,
    recurse => true,
    mode   => '0644',
    owner  => $httpd_user,
    group  => $httpd_user,
  }

}
