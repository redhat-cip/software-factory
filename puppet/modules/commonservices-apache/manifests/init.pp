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

  file {'/etc/apache2/sites-available/etherpad':
    ensure => file,
    mode   => '0640',
    owner  => 'www-data',
    group  => 'www-data',
    source =>'puppet:///modules/commonservices-apache/etherpad',
    notify => Service[apache2],
  }

  file { '/etc/apache2/sites-enabled/000-default':
    ensure => absent,
  }

  exec {'enable_etherpad_site':
    command => 'a2ensite etherpad',
    path    => '/usr/sbin/:/usr/bin/:/bin/',
    require => [File['/etc/apache2/sites-available/etherpad']],
    before  => Class['monit'],
  }

  service {'apache2':
    ensure     => running,
    enable     => true,
    hasrestart => true,
    hasstatus  => true,
    require    => Exec['enable_etherpad_site'],
  }

}
