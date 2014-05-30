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
  file {'/var/lib/jenkins/credentials.xml':
    ensure  => file,
    mode    => '0644',
    owner   => 'jenkins',
    group   => 'nogroup',
    content => template('jenkins/credentials.xml.erb'),
    require => User['jenkins'],
  }
  file {'/var/lib/jenkins/jenkins.model.JenkinsLocationConfiguration.xml':
    ensure  => file,
    mode    => '0644',
    owner   => 'jenkins',
    group   => 'nogroup',
    content => template('jenkins/jenkins.model.JenkinsLocationConfiguration.xml.erb'),
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
  file {'/var/lib/jenkins/config.xml':
    ensure  => file,
    mode    => '0644',
    owner   => 'jenkins',
    group   => 'nogroup',
    notify  => Service['jenkins'],
    content => template('jenkins/config.xml.erb'),
    require => [File['/var/lib/jenkins/credentials.xml'],
                File['/var/lib/jenkins/jenkins.model.JenkinsLocationConfiguration.xml'],
                File['/var/lib/jenkins/hudson.plugins.gearman.GearmanPluginConfig.xml'],
                File['/var/lib/jenkins/hudson.tasks.Mailer.xml'],
                File['/var/lib/jenkins/plugins/swarm-1.15.hpi']],
  }
  service { 'jenkins':
    ensure  => 'running',
    enable  => 'true',
  }
  package {'rubygems':
    ensure => 'installed',
  }
  package {'rake':
    ensure => 'installed',
  }
  package {'puppet-lint':
    ensure => 'installed',
  }
  package {'python-pip':
    ensure => 'installed',
  }
  package {'flake8':
    ensure   => 'installed',
    provider => 'pip',
    require  => Package['python-pip'],
  }
  package {'rspec-puppet':
    ensure   => 'installed',
    provider => 'gem',
    require  => Package['rubygems'],
  }

  file { '/etc/monit/conf.d/jenkins':
    ensure  => present,
    content => template('jenkins/monit.erb'),
    require => [Package['monit'], File['/etc/monit/conf.d']],
    notify  => Service['monit'],
  }
}
