redmine:
  :roles:
    - base
    - redmine
    - postfix
  :username: root
  :hostname: SF_PREFIX-redmine

mysql:
  :roles:
    - base
    - mysql
    - postfix
  :username: root
  :hostname: SF_PREFIX-mysql

ldap:
  :roles:
    - base
    - ldap
    - postfix
  :username: root
  :hostname: SF_PREFIX-ldap

gerrit:
  :roles:
    - base
    - gerrit
    - postfix
  :username: root
  :hostname: SF_PREFIX-gerrit

jenkins:
  :roles:
    - base
    - jenkins
    - postfix
  :username: root
  :hostname: SF_PREFIX-jenkins

commonservices:
  :roles:
    - base
    - commonservices
  :username: root
  :hostname: SF_PREFIX-commonservices

managesf:
  :roles:
    - base
    - managesf
  :username: root
  :hostname: SF_PREFIX-managesf
