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
   service { "jenkins":
     ensure  => "running",
     enable  => "true",
  }
  user { "jenkins":
     password => '$6$I.XrOOwo$lpbpxQnBMoHDZ2dpcsYZD.MzMjusR0JVt6nTld05TDMej0MHJeEzX0YVuhdlEk01jx.IZO8bAn4DIlrwDVtOQ1',
     groups => ['shadow'],
  }
  file {'/var/lib/jenkins/config.xml':
    ensure  => file,
    mode    => 0644,
    owner   => "jenkins",
    group   => "nogroup",
    notify  => Service["jenkins"],
    content => template('jenkins/config.xml.erb'),
  }
  file {'/var/lib/jenkins/credentials.xml':
    ensure  => file,
    mode    => 0644,
    owner   => "jenkins",
    group   => "nogroup",
    notify  => Service["jenkins"],
    content => template('jenkins/credentials.xml.erb'),
  }
  file {'/var/lib/jenkins/gerrit-trigger.xml':
    ensure  => file,
    mode    => '0644',
    owner   => "jenkins",
    group   => "nogroup",
    notify  => Service["jenkins"],
    content => template('jenkins/gerrit-trigger.xml.erb'),
  }
  file {'/var/lib/jenkins/jenkins.model.JenkinsLocationConfiguration.xml':
    ensure  => file,
    mode    => '0644',
    owner   => "jenkins",
    group   => "nogroup",
    notify  => Service["jenkins"],
    content => template('jenkins/jenkins.model.JenkinsLocationConfiguration.xml.erb'),
  }
  file {'/var/lib/jenkins/plugins/swarm-1.15.hpi':
    ensure  => file,
    mode    => '0644',
    owner   => "jenkins",
    group   => "nogroup",
    notify  => Service["jenkins"],
    source =>'puppet:///modules/jenkins/swarm-1.15.hpi',
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
    ensure => 'installed',
    provider => 'pip',
    require  => Package['python-pip'],
  }
  package {'rspec-puppet':
    ensure => 'installed',
    provider => 'gem',
    require  => Package['rubygems'],
  }
}
