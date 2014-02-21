class jenkins ($settings = hiera_hash('jenkins', '')) {
  file {'/var/lib/jenkins/config.xml':
    ensure  => file,
    mode    => 0644,
    owner   => "jenkins",
    group   => "nogroup",
    content => template('jenkins/config.xml.erb'),
  }
  file {'/var/lib/jenkins/credentials.xml':
    ensure  => file,
    mode    => 0644,
    owner   => "jenkins",
    group   => "nogroup",
    content => template('jenkins/credentials.xml.erb'),
  }
  file {'/var/lib/jenkins/gerrit-trigger.xml':
    ensure  => file,
    mode    => '0644',
    owner   => "jenkins",
    group   => "nogroup",
    content => template('jenkins/gerrit-trigger.xml.erb'),
  }
  file {'/etc/jenkins_jobs/jenkins_jobs.ini':
    ensure  => file,
    mode    => '0400',
    content => template('jenkins/jenkins_jobs.ini.erb'),
  }
}
