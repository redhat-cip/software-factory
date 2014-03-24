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
