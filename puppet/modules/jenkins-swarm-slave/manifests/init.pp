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
