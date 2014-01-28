edeploy-software-factory-roles
==============================

The edeploy roles for software factory roles.

Creating a bootable image
-------------------------

You need a configuration file for creating bootable images. For example:

	# Size of the root filesystem in MB or auto
	#ROOT_FS_SIZE=1000
	ROOT_FS_SIZE=auto

	# Output format supported by qemu-img
	# Use 'qemu-img --help | grep Supported | cut -d ":" -f2' to get the full list
	IMAGE_FORMAT=qcow2

	# Network Configuration
	# Only auto is supported now
	NETWORK_CONFIG=auto

Save this as "jenkins.virt". Now create an image:

	sudo make jenkins VIRTUALIZED=jenkins.virt

The image will be saved as `/var/lib/debootstrap/install/D7-H.1.0.0/jenkins-D7-H.1.0.0.img.qcow2`.

Registering image and booting VM
--------------------------------

Upload images to Glance (set OS_* before)

	glance -v image-create --name="eDeploy MySQL" --container-format ovf --disk-format qcow2 < /var/lib/debootstrap/install/D7-H.1.0.0/mysql-D7-H.1.0.0.img.qcow2 
	glance -v image-create --name="eDeploy Redmine" --container-format ovf --disk-format qcow2 < /var/lib/debootstrap/install/D7-H.1.0.0/redmine-D7-H.1.0.0.img.qcow2

Get image UUIDs:

	nova image-show "eDeploy MySQL"
	nova image-show "eDeploy Redmine"

Add required users and databases to mysql.cloudinit, start new VM using MySQL image:

 	nova boot --flavor 10 --image 0c9dfe66-2be7-46f8-90cf-dc2116df49be --user-data mysql.cloudinit --key_name cschwede edeploy-mysql

Get private IP from machine:

	nova show "edeploy-mysql"

Update private IP in redmine.cloudinit, start new VM using Redmine image:
	
	nova boot --flavor 10 --image 34e66e87-00a5-4852-ada8-8ac31d557c3e --user-data redmine.cloudinit --key_name cschwede --security-groups default,public-web edeploy-redmine

Assign floating IP to redmine VM:

	nova floating-ip-associate edeploy-redmine 198.154.188.219


Roles
-----

### Ldap

A sample openldap server have been setup in order to emulate a customer's users directory.
It is auto-configured with cloud-init with a simple schema, ie: ou=Users,dc=enovance,dc=com

### Gerrit

### Jenkins

What's need to be done automagically:

* Authentication: In /var/lib/jenkins/config.xml
..* Force authentication: <authorizationStrategy class="hudson.security.FullControlOnceLoggedInAuthorizationStrategy"/> 
..* ldap address: <server>ldap://10.43.0.61</server>
..* Root dn: <rootDN>dc=enovance,dc=com</rootDN>
..* Users base: <userSearchBase>ou=Users</userSearchBase>
..* User match: <userSearch>cn={0}</userSearch>

* Gerrit-trigger: In /var/lib/jenkins/gerrit-trigger.xml
..* Gerrit host: <gerritHostName>198.154.188.164</gerritHostName><gerritSshPort>29418</gerritSshPort>
..* Gerrit ssh-key: <gerritAuthKeyFile>/var/lib/jenkins/.ssh/id_rsa</gerritAuthKeyFile>

* Test-job

### Redmine

The role includes redmine and an apache web server. The initial database configuration is not done during image creation;
the database connection and schema creation will be done by puppet after the VM has booted.
cloud-init is used to set the IP address of the database host and to trigger puppet to finish the configuration.

### MySQL

This is a base role for a MySQL database server. After booting the VM cloud-init is used to create two databases and users
for Gerrit and Redmine.
