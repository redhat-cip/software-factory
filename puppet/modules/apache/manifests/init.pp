#
# Copyright (C) 2015 Red Hat
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

class apache () {

  require hosts

  $provider = 'systemd'
  $http = 'httpd'
  $httpd_user = 'apache'

  file {'00-ssl.conf':
    path    => '/etc/httpd/conf.modules.d/00-ssl.conf',
    content => 'LoadModule ssl_module modules/mod_ssl.so',
  }

  file {'ssl.conf':
    ensure => file,
    path   => '/etc/httpd/conf.d/ssl.conf',
    source => 'puppet:///modules/apache/ssl.conf',
    mode   => '0640',
    owner  => $httpd_user,
    group  => $httpd_user,
  }

  package { $http:
    ensure => present,
  }

  service {'webserver':
    ensure     => running,
    name       => $http,
    enable     => true,
    hasrestart => true,
    hasstatus  => true,
    provider   => $provider,
  }

}
