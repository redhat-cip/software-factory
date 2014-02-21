class jjb ($settings = hiera_hash('jenkins', '')) {
  file {'/etc/jenkins_jobs/jenkins_jobs.ini':
    ensure  => file,
    mode    => '0400',
    owner   => "jenkins",
    group   => "nogroup",
    content => template('jjb/jenkins_jobs.ini.erb'),
  }
}
