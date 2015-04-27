# Change Log

## 1.0.1 [unreleased]

## 1.0.0 2015-04-27

### Added

- Bump SF version to 1.0.0
- Enforce authentication for dashboard page if not logged in
- Redirect unauthenticated users trying to access Gerrit main
  page directly in Apache

### Fixed

- Fix missing topmenu in Jenkins.
- Fix missing topmenu in Redmine backlog.
- Fix typos in Readme.md


## 0.9.9 2015-04-27

Not released. Skipped version.


## 0.9.8 2015-04-27

Not released. Skipped version.


## 0.9.7 2015-03-31

### Added

- Support for github issues migration.
- Support for CSV issue migration.
- Make Redmine backlog available to non members by default.
- Add authentication with Github API key
- New top menu
- More keywords like "Closes", "Fix", "Related to" for
  Gerrit hooks.
- Add "recheck" hook in zuul for people used to the
  OpenStack workflow.
- Display amount of running tests per project in the sashboard.

### Fixed

- Add error message to the login page in case of wrong auth.
- Fix top menu missbehaviors

### Removed

- Cascading Apache between gateway and Gerrit (no more apache
  on Gerrit node)


## 0.9.6 2015-02-12

### Fixed

- Fix Github authentication filtered by organization when
  membership is private.
- SSL based authentications was not working properly
- Functional tests now clean old images after a successful run

### Added

- Allow to specify more than one nameserver during the HEAT
  deployment.
- Add an issue migration tool. Currently support migration
  from regular Redmine to SF Redmine. A section has been added in
  the documentation about that feature.
- Add an option to configure an automatic backup export to a
  Swift container.
- Add an option to hidden all services including Pastie, Etherpad
  and Zuul behind the authentication.
- Improve documentation about issue status update by the
  Gerrit hooks.

### Changed

- Heat stack now support multiple DNS and cidr for security groups


## 0.9.5 2015-02-03

### Fixed

- Fix httpd not started on the puppetmaster after a reboot
- Fix default Zuul layout.yaml for improving the Gate pipeline
  triggering.
- Handle empty email from Github for the Github auth.

### Added

- Support HTTPS and force a redirect if not used on the web UI.
- All nodes are synchronized by NTP when deployed on VMs (HEAT).
- Add section in the documentation to explain how to configure and
  connect a Jenkins slave.

### Changed

- Improve the Gerrit project replication configuration by avoiding
  the need to change /home/gerrit/.ssh/known_hosts and restart manually
  gerrit.
- Reduce downtime during the upgrade.
- Change Redmine MySQL connector to mysql2.

### Removed


## 0.9.4 2015-01-16

### Fixed

- Fix error displayed in dashboard when user is not known as project
  owner.
- Fix bug where Jenkins is restarted every 30 minutes by Puppet.

### Added

- Add a confirmation alert when trying to remove a project via the dashboard.
- Upgrade procedure for 0.9.3 to 0.9.4.

### Changed

- Upgrade Jenkins swarm plugin to 1.22.
- Upgrade Gerrit to 2.8.6.1.

### Removed


## 0.9.3 2014-12-31

### Fixed

- Fix usage of the back argument after a successful login.
- Fix Gerrit submit when more than two +2 core reviews.
- Fix Redmine backlog no working.
- Fix 406 error code on Gerrit when token expired.

### Changed

- Consolidate image build with some retry strategies when
  fetching remote components.
- Move to Jenkins LTS verion 1.580.

### Added

- Upgrade procedure for 0.9.2 to 0.9.3.
- Documentation for the upgrade process.
- Add a dashboard that display current projects and opened
  review as well as opened issues.
- Github authentication restricted by organizations

### Removed

- Debian support.


## 0.9.2 2014-11-25
- Initial release.
