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
                $cauth = hiera_hash("cauth", '')) {

  case $operatingsystem {
    centos: {
      $http = "httpd"
      $provider = "systemd"
      $httpd_user = "apache"

      package { $http:
        ensure => present,
      }

      file {'/etc/httpd/conf.d/managesf.conf':
        ensure => file,
        mode   => '0640',
        owner  => $httpd_user,
        group  => $httpd_user,
        content=> template('managesf/managesf.site.erb'),
        notify => Service['webserver'],
      }

      service {'webserver':
        name       => $http,
        ensure     => running,
        enable     => true,
        hasrestart => true,
        hasstatus  => true,
        provider   => $provider,
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
        source  => 'puppet:///modules/managesf/service_rsa',
        require => File['/usr/share/httpd/.ssh'],
      }
    }
    debian: {
      $http = "apache2"
      $provider = "debian"
      $httpd_user = "www-data"

      package { $http:
        ensure => present,
      }

      file { '/etc/apache2/sites-enabled/000-default':
        ensure => absent,
      }

      file {'/etc/apache2/sites-available/managesf':
        ensure => file,
        mode   => '0640',
        owner  => $httpd_user,
        group  => $httpd_user,
        content=> template('managesf/managesf.site.erb'),
      }

      exec {'enable_managesf_site':
        command => 'a2ensite managesf',
        path    => '/usr/sbin/:/usr/bin/:/bin/',
        require => [File['/etc/apache2/sites-available/managesf'],
                    File['/var/www/managesf/config.py']],
        notify => Service['webserver'],
      }

      service {'webserver':
        name       => $http,
        ensure     => running,
        enable     => true,
        hasrestart => true,
        hasstatus  => true,
        provider   => $provider,
        require    => Package[$http],
      }

# managesf can't access keys in /root/.ssh and can only
# access keys from /var/www/.ssh, so creating keys here
      file { '/var/www/.ssh':
        ensure  => directory,
        owner   => $httpd_user,
        group   => $httpd_user,
        mode    => '0755',
      }

      file { '/var/www/.ssh/id_rsa':
        ensure  => present,
        owner   => $httpd_user,
        group   => $httpd_user,
        mode    => '0600',
        source  => 'puppet:///modules/managesf/service_rsa',
        require => File['/var/www/.ssh'],
      }
    }

    }

  file { '/var/log/managesf/':
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
    source => 'puppet:///modules/managesf/gerrit_admin_rsa',
    require => File['/var/www/managesf/'],
  }

}
