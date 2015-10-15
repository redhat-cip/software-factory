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

class jenkins {

  require hosts

  $fqdn = hiera('fqdn')
  $auth = hiera('authentication')
  $url = hiera('url')
  $settings = hiera('jenkins')
  $jenkins_password = hiera('creds_jenkins_user_password')
  $admin_name = $auth['admin_name']
  $jenkins_rsa = hiera('jenkins_rsa')

  file {'/etc/httpd/conf.d/ports.conf':
    ensure => file,
    mode   => '0640',
    owner  => $::httpd_user,
    group  => $::httpd_user,
    source =>'puppet:///modules/jenkins/ports.conf',
  }

  file {'/etc/httpd/conf.d/jenkins.conf':
    ensure  => file,
    mode    => '0640',
    owner   => $::httpd_user,
    group   => $::httpd_user,
    content => template('jenkins/jenkins.site.erb'),
    require => [File['/etc/httpd/conf.d/ports.conf'],
        ],
    notify  => Exec['webserver_restart'],
  }

  exec { 'webserver_restart':
    command => '/usr/sbin/apachectl restart',
    require => File['/etc/httpd/conf.d/jenkins.conf'],
  }

  file {'/etc/init.d/jenkins':
    ensure  => 'absent',
  }

  file {'/lib/systemd/system/jenkins.service':
    ensure  => file,
    mode    => '0640',
    owner   => 'jenkins',
    group   => 'jenkins',
    content => template('jenkins/jenkins.service.erb'),
  }

  file { '/var/cache/jenkins':
      ensure  => directory,
      owner   => 'jenkins',
      group   => 'jenkins',
      require => [User['jenkins'], Group['jenkins']],
  }

  service { 'jenkins':
    ensure  => 'running',
    enable  => true,
    require => [File['/lib/systemd/system/jenkins.service'],
                File['/etc/init.d/jenkins'],
                File['/var/lib/jenkins'],
                File['/var/cache/jenkins'],
                File['/var/lib/jenkins/config.xml']],
  }

  exec { 'shutdown_jenkins':
    provider    => 'shell',
    command     => 'service jenkins stop',
    refreshonly => true,
  }

  user { 'jenkins':
    ensure  => present,
    require => Group['jenkins'],
  }

  group { 'jenkins':
    ensure => present,
  }

  file { '/var/lib/jenkins':
    ensure  => directory,
    owner   => 'jenkins',
    group   => 'jenkins',
    require => [User['jenkins'], Group['jenkins']],
  }

  file { '/var/lib/jenkins/.ssh':
      ensure  => directory,
      owner   => 'jenkins',
      group   => 'jenkins',
      require => [User['jenkins'], Group['jenkins']],
  }
  file { '/var/lib/jenkins/.ssh/id_rsa':
      ensure  => file,
      owner   => 'jenkins',
      group   => 'jenkins',
      mode    => '0400',
      content => inline_template('<%= @jenkins_rsa %>'),
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

  file {'/var/lib/jenkins/org.jenkinsci.plugins.ZMQEventPublisher.HudsonNotificationProperty.xml':
    ensure  => file,
    mode    => '0644',
    owner   => 'jenkins',
    group   => 'jenkins',
    source  => 'puppet:///modules/jenkins/org.jenkinsci.plugins.ZMQEventPublisher.HudsonNotificationProperty.xml',
    require => User['jenkins'],
  }

  file {'/etc/jenkins_admin.name':
    ensure  => file,
    content => inline_template('<%= @admin_name %>'),
    notify  => [Exec['shutdown_jenkins'], Exec['change_admin_name']],
  }

  exec {'change_admin_name':
    command     => "sed -i s/\"$(grep hudson.model.Hudson.Administer /var/lib/jenkins/config.xml | grep -v jenkins | sed -re 's/.+:(.+)<.+/\\1/g')\"/${admin_name}/ /var/lib/jenkins/config.xml",
    provider    => 'shell',
    refreshonly => true,
    notify      => Service['jenkins'],
    require     => Exec['shutdown_jenkins'],
    onlyif      => 'test -f /var/lib/jenkins/config.xml',
  }

  file {'/var/lib/jenkins/config.xml':
    ensure  => file,
    replace => false,
    mode    => '0644',
    owner   => 'jenkins',
    group   => 'jenkins',
    content => template('jenkins/config.xml.erb'),
    require => [File['/var/lib/jenkins/jenkins.model.JenkinsLocationConfiguration.xml'],
                File['/var/lib/jenkins/hudson.plugins.gearman.GearmanPluginConfig.xml'],
                File['/var/lib/jenkins/hudson.tasks.Mailer.xml'],
                File['/var/lib/jenkins/org.jenkinsci.main.modules.sshd.SSHD.xml'],
                File['/etc/sudoers.d/jenkins']],
  }

  file {'/var/lib/jenkins/credentials.xml':
    ensure  => file,
    replace => false,
    mode    => '0644',
    owner   => 'jenkins',
    group   => 'jenkins',
    source  => 'puppet:///modules/jenkins/credentials.xml',
    require => [File['/var/lib/jenkins/config.xml']],
  }

  file {'/var/lib/jenkins/org.codefirst.SimpleThemeDecorator.xml':
    ensure  => file,
    mode    => '0644',
    owner   => 'jenkins',
    group   => 'jenkins',
    source  => 'puppet:///modules/jenkins/org.codefirst.SimpleThemeDecorator.xml',
    require => User['jenkins'],
  }

  file {'/etc/sudoers.d/jenkins':
    ensure  => file,
    mode    => '0440',
    owner   => 'root',
    group   => 'root',
    source  => 'puppet:///modules/jenkins/sudoers_jenkins',
    replace => true,
  }

  file { 'wait4jenkins':
    path   => '/root/wait4jenkins.sh',
    mode   => '0740',
    source => 'puppet:///modules/jenkins/wait4jenkins.sh',
  }

  # This ressource wait for Jenkins to bee fully UP
  exec { 'wait4jenkins':
    path    => '/usr/bin:/usr/sbin:/bin',
    command => '/root/wait4jenkins.sh',
    timeout => 900,
    require => [File['wait4jenkins'],  Service['jenkins']],
  }

  exec {'jenkins_user':
    command => "/usr/bin/htpasswd -bc /etc/httpd/htpasswd jenkins ${jenkins_password}",
    creates => '/etc/httpd/htpasswd',
  }

  bup::scripts{ 'jenkins_scripts':
    name           => 'jenkins',
    backup_script  => 'jenkins/backup.sh.erb',
    restore_script => 'jenkins/restore.sh.erb',
  }
}
