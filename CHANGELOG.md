=============
Release Notes
=============

2.2.3 2016-07-20
================

A new service called storyboard is now available to manage issues and sprint board.

New Features
------------

- Add storyboard service (disabled by default)
- disable statsd by default
- make mariadb systemd dependency multihost-aware
- add a template job to upload a package to PyPI
- Gerritbot notification now suports the "change-created" event type to notify new change only, instead of every patchset.
- The storyboard webclient is available from the top-menu. Direct access to the API is possible with a cauth cookie, url is "fqdn/storyboard" api, userid is cauth id and the access token is the username.
- Add swift mirror service through config-repo. It uses mirror2swift to mirror http or rpm repodata contents.

Upgrade Notes
-------------

- To activate the storyboard service, the ansible roles (storyboard and storyboardclient) needs to be added to the arch.yaml hiera configuration file.
- To ensure nodepool test run on a fresh node, the zuul parameter-function is now set in the read only config/zuul/layout.yaml file. If the ^.*$ parameter function is set in another file, it needs to be manually removed in the upgrade proposed change "Upgrade of base config repository files".


Bug Fixes
---------

- prevent gnupg keyrings of the root user to be wiped during upgrade
- fix admin user update without username in gerrit
- fix issues when the FQDN is changed after the initial deployment
- prevent monit from restarting gerrit
- remove monit actions for redmine
- improve rebooting by ensuring all services are correctly restarted
- fix hook failure when commit message contains double quotes
- Set by default the amount of Jenkins master executors to 1. This prevent two config-update job to run in parallel.
- Nodepool logging for image-update command now properly print setup scripts stdout on terminal. Moreover service's logs were missing automatic rotation.

2.2.2 2016-06-21
================

New Features
------------

- Add commands related to the services users management. CRUD to deals with registered users on SF.
- An automatic groovy scripts will remove offline jenkins slave daily.
- Gerritbot channels configuration is now managed through the config-repo.


Upgrade Notes
-------------

- Fix mumble upgrade to keep TLS certificates and room created.
- Gerritbot channels.yaml configuration file will be automatically submitted to the configuration repo


Critical Issues
---------------

- Fix backup restore to properly reset mysql service user credencials.
- Fix nodepool paramiko incorrect version and logs of image-update command.


Bug Fixes
---------

- Change to request the api.github.com/users/emails for fetching user emails
- Support unicode full names in Gerrit and Redmine.
- Fix zuul_swift_upload.py artifact export on Swift no working since SF 2.2.1.
- Properly set postfix myhostname to the fqdn. To avoid Greylisting, operator needs to configure the reverse dns of public ip to the fqdn.
- Allow Gitweb access for public projects anonymously


Other Notes
-----------

- Removal of membership management for project/create endpoint in the CLI.
- Add the Gitweb kogakure theme by default.
- Nodepool upgrade to 1fd2a14ab79d256419083e2b2d9c463af36e039a (May 18, 2016 )


2.2.1  2016-05-23
=================

New Features
------------

- Keep track of external authenticated user (via OAuth/OpenID) and enable autosync of the primary user email to SF
- Gerrit replication configuration is now part of the config repository. Merged changed on "gerrit/replication.config" file will be taken into account by Gerrit without any restart.
- Documentation has been updated to reflect changes about the replication.


Upgrade Notes
-------------

- The replication.config file of gerrit will be proposed automatically to the config repository via Gerrit. This change must be approved as well as the change on the default JJB jobs against the config repository.
- Some home directories were managed by puppet User statement, which didn't get recreated after upgrade when user already exists. This release fix by ensuring directory are present before running puppet.


Deprecation Notes
-----------------

- Remove the replication management via the sfmanager CLI


Security Issues
---------------

- Upgrade jenkins to version 1.651.2 to mitigate Jenkins Security Advisory 2016-05-11.


Bug Fixes
---------

- Fix primary user email not fetched from Github
- Wrong documentation version number in the doc
- Fix some Redmine 404 errors
- Fix config-check that was unable to validate nodepool configuration when multiple cloud provider are used.


Other Notes
-----------

- Zuul upgraded to fdeb224824584dad355cbda207811a2105d1d2e2 (May 11 2016)
- Nodepool upgrade to e0f65825b0a38f8370017a08dd6f6012704d8db6 (May 11 2016)
- Set selinux labels when missing
- Top level http requests are now redirected by default to Gerrit instead of the dashboard


2.2.0  2016-04-08
=================

New Features
------------

- Document how to use custom certificate such as letsencrypt.
- Break down jenkins, jjb, zuul and nodepool role to be usable independently.
- Config-update is now an ansible playbook that updates each service remotely.
- Service extra configuration is now done with ansible to perform operation based on the host inventory.
- A new mumble service is activated by default.
- When nodepool is enabled, slaves are now put offline by default to avoid reuse. To keep a slave alive, jobs needs to explicitly use the "set_node_reuse" option.
- Add gearman-check tool
- Add playbook to rename seamlessly projects on SF
- Extend backup to include more data and add mechanism to encrypt backup before being exported
- Add doc example how to use Gerrit API
- Add doc how to use encrypted backups
- Project with namespace support such as skydive/server
- Add fundations for dynamic architecture based on Ansible
- Local users are now stored in Mariadb and now part of the backup
- Add fundations for sf pages feature
- Add fundations for jobs log exploration via ELK
- Add fundations to keep track of users comming from the SSO to avoid inconsistencies in the services DB
- Improve dashboard delay to display project listing
- Add Github repositories utils in sfmanager (create/delete/fork repo and add replication key)
- Break down jenkins, jjb, zuul and nodepool role to be usable independently.
- Config-update is now an ansible playbook that updates each service remotely.
- Service extra configuration is now done with ansible to perform operation based on the host inventory.
- A new mumble service is activated by default.
- When nodepool is enabled, slaves are now put offline by default to avoid reuse. To keep a slave alive, jobs needs to explicitly use the "set_node_reuse" option.


Known Issues
------------

- Nodepool now has its own copy of jenkins ssh key for slave management. Images private key needs to be updated to use /var/lib/nodepool/.ssh instead of jenkins.


Upgrade Notes
-------------

- System user/group id are now correctly updated according to ids.table definition. This is due to support upgrade from version prior 2.1.7 when image uid/gid were not consistent.


Bug Fixes
---------

- Backup operation was missing ssh key to succeed in multi-node environment.
- Continue Swift backup even if retention delete failed
- Fix gerritbot missing /var/run directory after reboot
- Some backup operations was allowed to normal user
- Better handling of Mariadb connections in ManageSF
- Backup operation was missing ssh key to succeed in multi-node environment.


2.1.8  2016-03-07
=================

This release fix the last errors observed in 2.1.7 and it may be the last 2.1.x release.


New Features
------------

- A new mumble service is activated by default.


Known Issues
------------

- Gerritbot service couldn't start because of /var/run permissions
- Etherpadd CSS was off by a few pixels
- Redmine redirection was broken after creating an issue
- Managesf was missing a setting to enable upload of replication ssh keys


Upgrade Notes
-------------

- System user/group id are now correctly updated according to ids.table definition. This is due to support upgrade from version prior 2.1.7 when image uid/gid were not consistent.



2.1.7  2016-02-21
=================

New Features
------------

- Add gerritbot
- Upgrade etherpad to 1.5.7


Known Issues
------------

- Remove redmine base_root_url to fix random 404
- Pin github3.py to avoid missing requirement error
- Fix dashboard if no longer authenticated

Security Issues
---------------

- Rebuild image to include CVE-2015-7547 fix
- Remove default etherpad admin credentials that may be used to reveal internal mysql password and sesion key.


2.1.6  2016-02-10
=================

This is a minor release to fix incorrect 2.1.5 build release (the .tgz file is actually from 2.1.4)


New Features
------------

- Use ansible to update known_hosts


Known Issues
------------

- Fix publish script to remove previous edeploy image
- Fix gearman service to zuul.fqdn
- Include zuul memory leak fix, see https://review.openstack.org/275483


2.1.5  2016-02-06
=================

This release feature a more recent nodepool version (upstream git master) to benefit from python-shade.


New Features
------------

- Two new options in sfconfig.yaml to enable/disable Github and Launchpad authentication
- Use managesf for user registration
- Heat template creates a network for nodepool slaves
- Nodepool cloud providers support setting a network which is required when multiple network are available
- Add CI toggle button to Gerrit
- Enable ansicolor plugin for jenkins
- Add reno support


Known Issues
------------

- Fix zuul to not run as root
- Fix broken Depends-On zuul logic
- Removed buggy check_rpm packages
- Fix wrong data type when creating account
- Various little fixes related to deletion of users on services


Upgrade Notes
-------------

- Update nodepool and zuul to last version (git master)


Security Issues
---------------

- Managesf and cauth directory was exposing gerrit admin access through http because of missing ACLs.
  Admin user password, Redmine API key, github client_secret and mysql local access may have leaked
  through non authenticated access to config.py. Please follow documentation instructions to
  regenerate thoses secrets, http://softwarefactory-project.io/docs/auths.html.


Other Notes
-----------

- Prevent pip to upgrade to pip-8
- Openstack integration tests now only need one tenant


# Legacy Change Log

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
