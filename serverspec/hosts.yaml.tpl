redmine:
  :roles:
    - base
    - redmine
  :username: root
  :hostname: SF_PREFIX-redmine

mysql:
  :roles:
    - base
    - mysql
  :username: root
  :hostname: SF_PREFIX-mysql

ldap:
  :roles:
    - base
    - ldap
  :username: root
  :hostname: SF_PREFIX-ldap

gerrit:
  :roles:
    - base
    - gerrit
  :username: root
  :hostname: SF_PREFIX-gerrit

jenkins:
  :roles:
    - base
    - jenkins
  :username: root
  :hostname: SF_PREFIX-jenkins

commonservices:
  :roles:
    - base
    - commonservices
  :username: root
  :hostname: SF_PREFIX-commonservices
