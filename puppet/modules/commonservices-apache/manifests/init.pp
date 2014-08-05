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

  package { 'apache2':
    ensure => present,
  }

  file {'/etc/apache2/sites-available/gateway':
    ensure => file,
    mode   => '0640',
    owner  => 'www-data',
    group  => 'www-data',
    content => template('commonservices-apache/gateway'),
    notify => Service[apache2],
  }

  file {'/var/www/index.py':
    ensure => file,
    mode   => '0740',
    owner  => 'www-data',
    group  => 'www-data',
    source  => 'puppet:///modules/commonservices-apache/index.py',
    notify => Service[apache2],
  }

  file {'/var/www/index.html.tmpl':
    ensure => file,
    mode   => '0640',
    owner  => 'www-data',
    group  => 'www-data',
    source  => 'puppet:///modules/commonservices-apache/index.html.tmpl',
    notify => Service[apache2],
  }

  file {'/var/www/bootstrap.min.css':
    ensure => file,
    mode   => '0640',
    owner  => 'www-data',
    group  => 'www-data',
    source  => 'puppet:///modules/commonservices-apache/bootstrap.min.css',
    notify => Service[apache2],
  }

  file {'/var/www/bootstrap.min.js':
    ensure => file,
    mode   => '0640',
    owner  => 'www-data',
    group  => 'www-data',
    source  => 'puppet:///modules/commonservices-apache/bootstrap.min.js',
    notify => Service[apache2],
  }

  file {'/var/www/jquery.min.js':
    ensure => file,
    mode   => '0640',
    owner  => 'www-data',
    group  => 'www-data',
    source  => 'puppet:///modules/commonservices-apache/jquery.min.js',
    notify => Service[apache2],
  }

  exec {'enable_gateway':
    command => 'a2ensite gateway',
    path    => '/usr/sbin/:/usr/bin/:/bin/',
    require => [File['/etc/apache2/sites-available/gateway']],
    before  => Class['monit'],
  }

  file { '/etc/apache2/sites-enabled/000-default':
    ensure => absent,
  }

  service {'apache2':
    ensure     => running,
    enable     => true,
    hasrestart => true,
    hasstatus  => true,
    require    => [Exec['enable_gateway'],]
  }

  file { '/var/www/static':
    ensure  => link,
    target  => '/srv/lodgeit/lodgeit/lodgeit/static/',
  }

}
