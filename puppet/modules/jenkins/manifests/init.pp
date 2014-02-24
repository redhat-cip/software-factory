class jenkins ($settings = hiera_hash('jenkins', '')) {
   service { "jenkins":
     ensure  => "running",
     enable  => "true",
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
  file {'/var/lib/jenkins/plugins/swarm-1.15.hpi':
    ensure  => file,
    mode    => '0644',
    owner   => "jenkins",
    group   => "nogroup",
    notify  => Service["jenkins"],
    source =>'puppet:///modules/jenkins/swarm-1.15.hpi',
  }
}
