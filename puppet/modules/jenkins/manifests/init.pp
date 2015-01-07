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

  require hosts

  $jenkins_password = $settings['jenkins_password']

  $http = "httpd"
  $provider = "systemd"
  $httpd_user = "apache"
  $htpasswd = "/etc/httpd/htpasswd"

  file {'/etc/httpd/conf.d/ports.conf':
    ensure => file,
    mode   => '0640',
    owner  => $httpd_user,
    group  => $httpd_user,
    source =>'puppet:///modules/jenkins/ports.conf',
  }

  file {'/etc/httpd/conf.d/jenkins.conf':
    ensure => file,
    mode   => '0640',
    owner  => $httpd_user,
    group  => $httpd_user,
    content => template('jenkins/jenkins.site.erb'),
    require => File['/etc/httpd/conf.d/ports.conf'],
    notify => Service['webserver'],
  }

  file {'/etc/init.d/jenkins':
    ensure  => 'absent',
  }

  file {'/lib/systemd/system/jenkins.service':
    ensure => file,
    mode   => '0640',
    owner  => $httpd_user,
    group  => $httpd_user,
    content => template('jenkins/jenkins.service.erb'),
  }

  file { "/var/cache/jenkins":
      ensure => directory,
      owner => "jenkins",
      group => "jenkins",
      require => [User['jenkins'], Group['jenkins']],
  }

  service { 'jenkins':
    ensure  => 'running',
    enable  => 'true',
    require => [File['/lib/systemd/system/jenkins.service'],
                File['/etc/init.d/jenkins'],
                File['/var/lib/jenkins'],
                File['/var/cache/jenkins']]
   }

  service {'webserver':
    name    => $http,
    ensure  => running,
    enable  => 'true',
    require => [Package[$http],
                File['/etc/httpd/conf.d/jenkins.conf'],
                File['/etc/httpd/conf.d/ports.conf']]
  }

  user { 'jenkins':
    ensure  => present,
    require => Group['jenkins'],
  }

  group { 'jenkins':
    ensure => present,
  }

  file { "/var/lib/jenkins":
      ensure => directory,
      owner => "jenkins",
      group => "jenkins",
      require => [User['jenkins'], Group['jenkins']],
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
    group   => 'jenkins',
    content => template('jenkins/jenkins.model.JenkinsLocationConfiguration.xml.erb'),
    require => User['jenkins'],
  }
  file {'/var/lib/jenkins/hudson.plugins.git.GitSCM.xml':
    ensure  => file,
    mode    => '0644',
    owner   => 'jenkins',
    group   => 'jenkins',
    content => template('jenkins/hudson.plugins.git.GitSCM.xml.erb'),
    require => User['jenkins'],
  }
  file {'/var/lib/jenkins/hudson.plugins.gearman.GearmanPluginConfig.xml':
    ensure  => file,
    mode    => '0644',
    owner   => 'jenkins',
    group   => 'jenkins',
    source  => 'puppet:///modules/jenkins/gearman_config.xml',
    require => User['jenkins'],
  }
  file {'/var/lib/jenkins/hudson.tasks.Mailer.xml':
    ensure  => file,
    mode    => '0644',
    owner   => 'jenkins',
    group   => 'jenkins',
    content => template('jenkins/hudson.tasks.Mailer.xml'),
    require => User['jenkins'],
  }
  file {'/var/lib/jenkins/org.jenkinsci.main.modules.sshd.SSHD.xml':
    ensure  => file,
    mode    => '0644',
    owner   => 'jenkins',
    group   => 'jenkins',
    source  => 'puppet:///modules/jenkins/org.jenkinsci.main.modules.sshd.SSHD.xml',
    require => User['jenkins'],
  }
  file {'/var/lib/jenkins/plugins/swarm-1.15.hpi':
    ensure  => file,
    mode    => '0644',
    owner   => 'jenkins',
    group   => 'jenkins',
    source  =>'puppet:///modules/jenkins/swarm-1.15.hpi',
    require => User['jenkins'],
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
                File['/var/lib/jenkins/org.jenkinsci.main.modules.sshd.SSHD.xml'],
                File['/etc/sudoers.d/jenkins']],
  }

  file {'/etc/sudoers.d/jenkins':
    ensure  => file,
    mode    => '0440',
    owner   => 'root',
    group   => 'root',
    source  => 'puppet:///modules/jenkins/sudoers_jenkins',
    replace => true
  }

  file { '/etc/monit/conf.d/jenkins':
    ensure  => present,
    content => template('jenkins/monit.erb'),
    require => [Package['monit'], File['/etc/monit/conf.d']],
    notify  => Service['monit'],
  }

  file { 'wait4jenkins':
    path    => '/root/wait4jenkins.sh',
    mode    => '0740',
    source  => 'puppet:///modules/jenkins/wait4jenkins.sh',
  }

  # This ressource wait for Jenkins to bee fully UP
  exec { 'wait4jenkins':
    path    => '/usr/bin:/usr/sbin:/bin',
    command => '/root/wait4jenkins.sh',
    timeout => 900,
    require => [File['wait4jenkins'],  Service['jenkins']],
  }

  exec {'jenkins_user':
    command   => "/usr/bin/htpasswd -bc $htpasswd jenkins $jenkins_password",
    require   => Package[$http],
    subscribe => Package[$http],
    creates => $htpasswd,
  }

  package { $http:
    ensure => present,
  }

  bup::scripts{ 'jenkins_scripts':
    backup_script => 'jenkins/backup.sh.erb',
    restore_script => 'jenkins/restore.sh.erb',
  }
}
