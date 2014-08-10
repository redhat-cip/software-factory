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

class jenkins ($settings = hiera_hash('jenkins', '')) {
  $jenkins_password = $settings['jenkins_password']

  user { 'jenkins':
    ensure   => present,
  }

  group { 'jenkins':
    ensure => present,
  }

  file { "/var/lib/jenkins/.ssh":
      ensure => directory,
      owner => "jenkins",
      group => "jenkins",
      require => [User['jenkins'], Group['jenkins']],
  }
  file { "/var/lib/jenkins/.ssh/id_rsa":
      ensure  => file,
      owner   => "jenkins",
      group   => "jenkins",
      mode    => 0400,
      source  => 'puppet:///modules/jenkins/jenkins_rsa',
      require => File['/var/lib/jenkins/.ssh'],
  }
  file {'/var/lib/jenkins/jenkins.model.JenkinsLocationConfiguration.xml':
    ensure  => file,
    mode    => '0644',
    owner   => 'jenkins',
    group   => 'nogroup',
    content => template('jenkins/jenkins.model.JenkinsLocationConfiguration.xml.erb'),
    require => User['jenkins'],
  }
  file {'/var/lib/jenkins/hudson.plugins.git.GitSCM.xml':
    ensure  => file,
    mode    => '0644',
    owner   => 'jenkins',
    group   => 'nogroup',
    content => template('jenkins/hudson.plugins.git.GitSCM.xml.erb'),
    require => User['jenkins'],
  }
  file {'/var/lib/jenkins/hudson.plugins.gearman.GearmanPluginConfig.xml':
    ensure  => file,
    mode    => '0644',
    owner   => 'jenkins',
    group   => 'nogroup',
    source  => 'puppet:///modules/jenkins/gearman_config.xml',
    require => User['jenkins'],
  }
  file {'/var/lib/jenkins/hudson.tasks.Mailer.xml':
    ensure  => file,
    mode    => '0644',
    owner   => 'jenkins',
    group   => 'nogroup',
    content => template('jenkins/hudson.tasks.Mailer.xml'),
    require => User['jenkins'],
  }
  file {'/var/lib/jenkins/plugins/swarm-1.15.hpi':
    ensure  => file,
    mode    => '0644',
    owner   => 'jenkins',
    group   => 'nogroup',
    source  =>'puppet:///modules/jenkins/swarm-1.15.hpi',
    require => User['jenkins'],
  }
  file {'/etc/default/jenkins':
    ensure  => file,
    mode    => '0644',
    owner   => 'root',
    group   => 'root',
    source  => 'puppet:///modules/jenkins/etc_default_jenkins',
    replace => true
  }
  file {'/etc/sudoers.d/jenkins':
    ensure  => file,
    mode    => '0440',
    owner   => 'root',
    group   => 'root',
    source  => 'puppet:///modules/jenkins/sudoers_jenkins',
    replace => true
  }
  file {'/var/lib/jenkins/config.xml':
    ensure  => file,
    mode    => '0644',
    owner   => 'jenkins',
    group   => 'jenkins',
    notify  => Service['jenkins'],
    content => template('jenkins/config.xml.erb'),
    require => [File['/var/lib/jenkins/jenkins.model.JenkinsLocationConfiguration.xml'],
                File['/var/lib/jenkins/hudson.plugins.gearman.GearmanPluginConfig.xml'],
                File['/var/lib/jenkins/hudson.tasks.Mailer.xml'],
                File['/var/lib/jenkins/plugins/swarm-1.15.hpi'],
                File['/etc/sudoers.d/jenkins'],
                File['/etc/default/jenkins']],
  }
  service { 'jenkins':
    ensure  => 'running',
    enable  => 'true',
  }

  file { '/etc/monit/conf.d/jenkins':
    ensure  => present,
    content => template('jenkins/monit.erb'),
    require => [Package['monit'], File['/etc/monit/conf.d']],
    notify  => Service['monit'],
  }

  package { 'apache2':
    ensure => present,
  }

  service {'apache2':
    ensure  => running,
    require => Package['apache2'],
  }

  file {'/etc/apache2/sites-available/jenkins':
    ensure => file,
    mode   => '0640',
    owner  => 'www-data',
    group  => 'www-data',
    source =>'puppet:///modules/jenkins/jenkins.site',
  }

  file { '/etc/apache2/sites-enabled/000-default':
    ensure => absent,
  }

  file {'/etc/apache2/ports.conf':
    ensure => file,
    mode   => '0640',
    owner  => 'www-data',
    group  => 'www-data',
    source =>'puppet:///modules/jenkins/apache-ports.conf',
  }

  exec {'jenkins_user':
    command   => "/usr/bin/htpasswd -bc /etc/apache2/htpasswd jenkins $jenkins_password",
    require   => Package['apache2'],
    subscribe => Package['apache2'],
    creates => "/etc/apache2/htpasswd",
  }

  exec { 'a2enmod_headers':
    command   => "/usr/sbin/a2enmod headers",
    require   => Package['apache2'],
    subscribe => Package['apache2'],
    refreshonly => true,
  }

  exec { 'a2enmode_proxy':
    command   => "/usr/sbin/a2enmod proxy",
    require   => Package['apache2'],
    subscribe => Package['apache2'],
    refreshonly => true,
  }

  exec { 'a2enmode_proxy_http':
    command   => "/usr/sbin/a2enmod proxy_http",
    require   => Package['apache2'],
    subscribe => Package['apache2'],
    refreshonly => true,
  }

  exec {'enable_jenkins_site':
    command => 'a2ensite jenkins',
    path    => '/usr/sbin/:/usr/bin/:/bin/',
    require => [File['/etc/apache2/sites-available/jenkins'],
                File['/etc/apache2/ports.conf'],
                Exec['jenkins_user']],
    notify => Service[apache2],
  }
}
