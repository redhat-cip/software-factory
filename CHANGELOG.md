# Change Log

## 2.1.4 2016-01-21

### Added

- Nosetimer to functional tests
- Packages list used in image build
- Gerrit backend user deletion
- Swift temp url key setting for zuul artifact upload
- Project creation can now import branch
- rpm-requirements and rpm-test-requirements script to install required package to build or use software-factory

### Changed

- Project owner can now push tags
- More pip and gems packages have been replaced by rpm
- Zuul and nodepool requirements are isolated using venv
- Move redmine installation to /var/www
- Pip installation is now capped at 'pip<8'
- Hide create project button if user isn't allowed

### Fixed

- Error when adding users with specific domain endings like .org
- Project creation failing when starting with the letter 'a'
- New flake8 errors related to recent version
- Monit monitoring of postfix
- Zuul was missing swift and keystone client
- Edeploy useradd/groupadd replacement was missing
- Gpg check condition was incorrect
- Functional tests are now re-entrant and can be run multiple time
- Number of open issues in dashboard was capped by redmine page limit

### Removed

- Ruby gem doc rdoc
- Build requirements from image (such as gcc, -devel, ...)
- Puppetlab repos since rdo also provide puppet


## 2.1.3 2016-01-14

### Added

- Integration tests with ansible for swift artifacts export, nodepool and zuul
- Rdo repository to install openstack python clients and gnocchi

### Changed

- Default heat template network and disk size to avoid conflict with integration tests
- Functional tests run zuul integration playbook
- Subprocess call in functional tests now print output
- Many requirements are now installed with rpm instead of pip
- All pip packages are now listed in third_party_tools as a global-requirements list

### Fixed

- Top-menu in etherpad and paste services was missing
- Redmine gateway.common configuration (contained two //)
- Monit monitoring of gerrit
- Backup command bup PATH was incorrect
- Skip gracefully if a project already exists in a service at project creation

### Removed

- Many image build left-overs that are unused
- Functional tests venv is now replaced by packages install in --user


## 2.1.2 2016-01-08

### Fixed

- Incorrect redmine relative_url_root setting
- Incorrect postfix restart command during upgrade
- Restart grafana-server after upgrade
- Fix config update review to not remove user data

## 2.1.1 2016-01-06

### Added

- python-testrepository and tmux to the base image

### Changed

- sfconfig.sh now uses ansible to perform extra configuration task
- ntp is enabled by default

### Fixed

- Nodepool version downgraded to 0.1.1
- Managesf and pysflib error debugging
- sfconfig.sh usage from cloudinit (set default HOME=/root)

## 2.1.0 2015-12-22

### Added

- New auto backup parameter to support Swift V1 auth: os_auth_version

### Changed

- Outgoing mail origin changed from managesf.fqdn to fqdn
- Use hooks REST API from managesf
- Gerrit upgraded to 2.11.5

### Fixed

- /etc/hosts order now uses aliases instead of duplicate entry for vhost
- serverspec tests
- better support of http proxies used by image building
- auto_backup template swift container templating

### Removed

- Unused puppet files

## 2.0.4 2015-12-21

### Added

- Ldap disable option
- Openstack based tests support (functional tests of heat deployment)
- Jenkins ansicolor plugin
- Support for http_proxy for image building
- Hiera edit --eval parameter to support complex structure like json dictionaries

### Changed

- Monit configuration
- Default tests domain changed to sftests.com

### Fixed

- Bug when using more than one nodepool provider
- Upgrade bootloader issue
- Links and documentations error
- Api access for managesf during Heat deployment
- Bundler update fix

## 2.0.3 2015-11-19

### Added

- Dashboard plugin in Jenkins
- Graphite/Grafana+StatsD integrated in SF dashboard

### Fixed

- Heat templates usage of sfconfig.sh for fqdn setting
- Typo in nodepool configuration causing KeyError
- Image build failure now properly abord current job
- Heat template incorect use of sfconfig.sh configuration script

### Changed

- Prepare managesf service plugins
- Default SSH timeout in nodepool set to 120 seconds

### Removed

- Deprecated backup/restore commands


## 2.0.2 2015-10-23

### Added

- disabled setting for nodepool and swift
- Multi providers support for Nodepool

### Changed

- Removed default root password to ease console access

### Fixed

- python-redmine version capped
- Fix incorrect jenkins url in gerrit comment
- Avoid manual step to configure Nodepool provider
- Fix init test feature of managesf

### Removed

- Admin name settings, it is now forced to "admin"
- public_ip settings for nodepool


## 2.0.1 2015-10-16

### Fixed

- Puppet manifest lint
- Redirection url and redmine/gerrit access

### Changed

- Renamed bootstraps scripts to sfconfig.sh
- Moved configuration script from /root to /usr/local/bin
- Default configuration is /etc/puppet/sf/hiera/sfconfig.yaml
- sfconfig refactored

### Added

- admin_mail_forward setting to forward notification mail
- allowed_proxy_prefixes setting to proxify logs access
- topmenu_custom_entry setting to set a custom link in top-menu

### Removed

- Admin real name and mail setting

## 2.0.0 2015-10-07

SF v2 is a major refactor to make deployment more modular.

### Added

- Backup and restore tests
- All in one deployment mode
- Adds custom logo and favicon support
- Add the mechanics to allow logs/artifacts export in Swift
- Add a allinone HEAT template
- Allow domain to change easily via sfconfig.yaml
- Allow admin username to be change via sfconfig.yaml

### Changed

- Bootstrap do puppet apply instead of agent
- Only support all-in-one and 2node deployment
- Image building system without edeploy
- Functional tests run from host
- Puppet manifest refactor to be avoid conflict when used together
- Managesf CLI refactor

### Removed

- Cloud-init bootstrap
- Puppetmaster and install server
- Edeploy-roles
- Puppet agent

## 1.0.4 2015-09-09

- Fix overlayfs usage in LXC deployment

## 1.0.3 2015-09-04

### Added

- Add binding credentials plugin in Jenkins
- Add Launchpad Login
- Add nodepool support
- Add links to Depends-On changeIDs in gerrit
- Add tooltips to dashboard links/buttons

### Fixed

- Fix htpasswd dashboard button
- Harmonize managesf CLI commands

### Removed

- Remove unused gerrit-git-prep.sh script

### Changed

- Allow anonymous access to Gerrit
- Allow anonymous access to Jenkins
- Allow anonymous access to Redmine
- Non admin user can''t create project

## 1.0.2 2015-07-12

### Added

- Zuul-cloner for subprojects fetching

### Fixed

- Documentation errors
- Fix jenkins configuration page with new top menu
- External libs building//testing

### Removed

- Unused rspec test of puppet modules

### Changed

- Support CentOS for host system instead of Ubuntu
- Default workflow changed to allow only 1 +2CR to merge change

## 1.0.1 2015-06-12

### Added

- Add option to hide entries in the topmenu.
- Add for support of locally defined users via
  managesf and cauth.
- Add Gerrit API accessible via basic auth.
- Add a Managesf command to create a password
  to access Gerrit API.
- Add a UI button to create a password to access
  Gerrit API.

### Fixed

- Add some defaults for the Redmine backlog plugin.
- Prevent 404 when direct access to gitweb.
- Set gerrit and redmine databases charsets to UTF8.
- Fix cookie state_mapping.db path.
- Skip role rebuilding if nothing changed.

### Changed

- Managesf, pysflib and cauth has been externalized
  from software-factory source code.
- Bump zuul version to the most recent one
  (fd463c84bfb342701061fe383c6d17e7a1bd4786 # 15/05/2015).

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
