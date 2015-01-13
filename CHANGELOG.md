# Change Log

## 0.9.5 [unreleased]
### Fixed
### Added
### Changed
### Removed

## 0.9.4 [unreleased]
### Fixed
- Fix error displayed in dashboard when user is not know as project
  owner.
- Fix bug where Jenkins is restart every 30 minutes by Puppet.
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
