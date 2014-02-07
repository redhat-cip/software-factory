redmine:
  :roles:
    - base
    - redmine
  :hostname: redmine_ip

mysql:
  :roles:
    - base
    - mysql
  :hostname: mysql_ip

ldap:
  :roles:
    - base
    - ldap
  :hostname: ldap_ip

gerrit:
  :roles:
    - base
    - gerrit
  :hostname: gerrit_ip

jenkins:
  :roles:
    - base
    - jenkins
  :hostname: jenkins_ip
