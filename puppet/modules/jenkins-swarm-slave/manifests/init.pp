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

class jenkins-swarm-slave ($settings = hiera_hash('jenkins', '')) {
  file {'/var/lib/jenkins/swarm-client-1.15-jar-with-dependencies.jar':
    ensure  => file,
    mode    => 0755,
    source =>'puppet:///modules/jenkins-swarm-slave/swarm-client-1.15-jar-with-dependencies.jar',
  }
  file {'/etc/default/jenkins-swarm-slave':
    ensure  => file,
    mode    => 0644,
    owner   => "jenkins",
    group   => "nogroup",
    content => template('jenkins-swarm-slave/etc_jenkins-swarm-slave'),
    require  => File['/var/lib/jenkins/swarm-client-1.15-jar-with-dependencies.jar'];
  }
  file {'/etc/init.d/jenkins-swarm-slave':
    ensure  => file,
    mode    => 0755,
    source =>'puppet:///modules/jenkins-swarm-slave/initd_jenkins-swarm-slave',
    require  => File['/var/lib/jenkins/swarm-client-1.15-jar-with-dependencies.jar'];
  }
  service { "jenkins-swarm-slave":
    enable  => "true",
    require  => File['/etc/init.d/jenkins-swarm-slave'];
  }
}
