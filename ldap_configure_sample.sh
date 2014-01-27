#!/bin/sh
#
# Simple ldap configuration:
#
# user_tree_dn = ou=Users,dc=openstack,dc=org
# user_objectclass = inetOrgPerson
# Admin user / password = cn=admin,dc=enovance,dc=com / ldappass
# User password = userpass


# Create users ou
cat <<EOF > users_ou.ldif
dn: ou=Users,dc=enovance,dc=com
objectClass: organizationalUnit
ou: Users
EOF

ldapadd -x -D cn=admin,dc=enovance,dc=com -w ldappass  -f /tmp/users_ou.ldif

# Create users
cat <<EOF > demo_users.ldif
dn: cn=demo_user1,ou=Users,dc=enovance,dc=com
cn: demo_user1
objectClass: person
sn: Demo user1
userPassword: userpass
objectClass: inetOrgPerson

dn: cn=demo_user2,ou=Users,dc=enovance,dc=com
cn: demo_user2
objectClass: person
sn: Demo user2
userPassword: userpass
objectClass: inetOrgPerson
EOF

ldapadd -x -D cn=admin,dc=enovance,dc=com -w ldappass  -f /tmp/demo_users.ldif

