class jenkins ($settings = hiera_hash('jenkins', '')) {
  file {'/var/lib/jenkins/config.xml':
    ensure  => file,
    mode    => 0644,
    owner   => "jenkins",
    group   => "nogroup",
    content => template('jenkins/config.xml.erb'),
  }
  file {'/etc/jenkins_jobs/jenkins_jobs.ini':
    ensure  => file,
    mode    => '0400',
    content => template('jenkins/jenkins_jobs.ini.erb'),
  }
}
