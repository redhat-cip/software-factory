class jenkins {
  file {'/var/lib/jenkins/config.xml':
    ensure  => file,
    mode => 0644,
    owner => "jenkins",
    group => "nogroup",
    content => template('jenkins/config.xml'),
  }
}
