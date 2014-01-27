# Authentication, in /var/lib/jenkins/config.xml:
  <authorizationStrategy class="hudson.security.FullControlOnceLoggedInAuthorizationStrategy"/>
  <securityRealm class="hudson.security.LDAPSecurityRealm" plugin="ldap@1.6">
    <server>ldap://10.43.0.61</server>
    <rootDN>dc=enovance,dc=com</rootDN>
    <inhibitInferRootDN>false</inhibitInferRootDN>
    <userSearchBase>ou=Users</userSearchBase>
    <userSearch>cn={0}</userSearch>
    <disableMailAddressResolver>false</disableMailAddressResolver>
  </securityRealm>

