redmine:
  :roles:
    - base
    - redmine
    - postfix
  :username: root
  :hostname: redmine.SF_SUFFIX

mysql:
  :roles:
    - base
    - mysql
    - postfix
  :username: root
  :hostname: mysql.SF_SUFFIX

ldap:
  :roles:
    - base
    - ldap
    - postfix
  :username: root
  :hostname: ldap.SF_SUFFIX

gerrit:
  :roles:
    - base
    - gerrit
    - postfix
  :username: root
  :hostname: gerrit.SF_SUFFIX

jenkins:
  :roles:
    - base
    - jenkins
    - postfix
  :username: root
  :hostname: jenkins.SF_SUFFIX

commonservices:
  :roles:
    - base
    - commonservices
  :username: root
  :hostname: commonservices.SF_SUFFIX

managesf:
  :roles:
    - base
    - managesf
  :username: root
  :hostname: managesf.SF_SUFFIX
