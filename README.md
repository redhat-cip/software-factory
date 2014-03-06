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

Install pigz before building to speed up the image compression.

Save this as "jenkins.virt". Now create an image:

	sudo make jenkins VIRTUALIZED=jenkins.virt

The image will be saved as `/var/lib/debootstrap/install/D7-H.1.0.0/jenkins-D7-H.1.0.0.img.qcow2`.


Deployment stages
-----------------

* eDeploy: Image creation
* LXC/eNocloud: Image boot
* cloudinit: Create static configuration + puppetmaster server address
* *puppetmaster* can be configured
* Each role first register their IP address to puppetmaster
* *Ldap* / *Mysql* can be configured
* Redmine register its api access key
* *Gerrit* can be configured
* *Redmine* can be configured
* Jenkins register its ssh public key
* *Jenkins* / *Jenkins-slave* can be configured


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

Using edeploy-lxc
-----------------

Edeploy-lxc can also be used to quickly test created roles:

	sudo edeploy-lxc --config sf-lxc.yaml restart

All containers should be started and should be accessible using embedded ssh-server, using ip address defined in the yaml file. Ie: to access the sf-ldap role:

	ssh root@192.168.134.50

Roles
-----

### Ldap

A sample openldap server have been setup in order to emulate a customer's users directory.
It is auto-configured with cloud-init with a simple schema, ie: ou=Users,dc=enovance,dc=com

### MySQL

This is a base role for a MySQL database server. By default it listens on 0.0.0.0 and can be used by other VMs in the same subnet.
After booting the VM cloud-init is used to create two databases and users for Gerrit and Redmine.

### Gerrit

The eDeploy image is provided with the Gerrit war and a gerrit user in it. Gerrit configuration
is done after the VM is booted. Gerrit configuration is handled by puppet and puppet need some
environment variables configured like the MySQL and LDAP database connection. All the available
variable are configurable in the gerrit_configure_sample.sh script.

This role need to be fully automated by cloud-init like it is done for the Redmine role. Configuration
variables and puppet triggering will be done by cloud-init.

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
..* This must be done for every-project and every-branches
..* We need Jenkins Job Builder
..* After job is configured for a gerrit project, the job does:
```shell
git fetch ${GIT_URL} ${GERRIT_REFSPEC} && git checkout FETCH_HEAD
nosetests
```


### Redmine

The role includes redmine and an apache web server. The initial database configuration is not done during image creation;
the database connection and schema creation will be done by puppet after the VM has booted.
cloud-init is used to set the IP address of the database host and to trigger puppet to finish the configuration.


Testing VMs with serverspec
---------------------------

From http://serverspec.org:
> With serverspec, you can write RSpec tests for checking your servers are configured correctly.
> 
> Serverspec tests your servers' actual state through SSH access, so you don't need to install any agent softwares on your servers and can use any configuration management tools, Puppet, Chef, CFEngine and so on.

Install required packages:

	apt-get install rubygems rake
	gem install serverspec rspec

Set appropriate settings in ``hosts.yaml`` and run tests:

	cd serverspec
	rake spec -j 10 -m

Gerrit replication
------------------

Replication plugin allows to automatically replicate repositories
on a remote SSH mirror. All repositories can be mirrored or only
a subset. The plugin is not provided in the gerrit.war and must
be built.

How to build it:

	-> Install ant, openjdk, javac ...

	-> Build and install Buck
	git clone https://gerrit.googlesource.com/buck
	ant
	ln -s bin/buck /usr/local/bin/buck

	-> Build Gerrit
	git clone --recursive https://gerrit.googlesource.com/gerrit
	git checkout <branch-stable>
	git submodule update
	git clean -fdx
	buck build gerrit

	-> Build the plugin
	buck build plugins/replication:replication
	ls buck-out/gen/plugins/replication/replication.jar
	
How to install it:

	scp buck-out/gen/plugins/replication/replication.jar user@gerrit:/tmp
	ssh -p 29418 user@gerrit gerrit plugin install /tmp/replication.jar

How to configure it:
The plugin need a configuration file ${site_path}/etc/replication.config. The simplest
example is as follow :

	[remote "mirror"]
  	url = fabien@192.168.134.1:replication/${name}.git
  	push = +refs/heads/*:refs/heads/*
  	push = +refs/tags/*:refs/tags/*

The plugin needs to find the private key to connect to the remote ssh and
will look at ~.ssh/config :

	Host 192.168.134.1
  	User fabien
  	IdentityFile /home/gerrit/site_path/etc/ssh_host_rsa_key
  	PreferredAuthentications publickey

The .ssh/known_hosts must be filled with the remote host key before Gerrit start to avoid
Gerrit replication plugin to refuse the connection. The file can be filled that way :

	ssh-keyscan -t rsa 192.168.134.1 >> ~/.ssh/known_hosts

A manual replication can be started as follow or a marged changed will triggered
a push on the remotes:

	ssh -p 29418 user@gerrit replication start --all

I tried with Github and it works as expected. The main differences between Github
and a self-managed Git repo server is that the replication plugin is able to create
a missing repository on the self-managed Git server and not on Github. That means
the repositories to replicate must be created before on Github.

Use eDeploy to upgrade roles
----------------------------

In SF the upgrade of the running roles (Redmine, Jenkins, Gerrit, ...) will
be managed by eDeploy. That why along with the others roles in the SF we
have a role edeploy-server deployed on the target IAAS.

The eDeploy server role contains in /var/lib/debootstrap/install all the
file trees for each role of the SF (base roles + updated roles).
/var/lib/debootstrap/metadata contains the update rules in form
of directories name like D7-H.1.0.0/ldap/D7-H.1.0.1 that contains
files (add_only, exclude, pre, post). The eDeploy server role serves
via rsync install and metadata directories.

Each role built with eDeploy automatically have a script /usr/sbin/edeploy.
This script is used to verify the availability of an upgrade as well as
performing the upgrade of the local file system. 

        root@sf-ldap:~# edeploy list
        D7-H.1.0.1

        root@sf-ldap:~# edeploy upgrade D7-H.1.0.1
        ...
        Upgraded to D7-H.1.0.1

The add_only and exclude files are used by rsync during the file system
tree retreival. The pre and post script are triggered respectively before
and after the file retreival. In those files you can for example stop/start
services in case of services' configuration files has changed.

How to build an upgrade role with eDeploy for the SF
----------------------------------------------------

In the edeploy directory of SF there is a script called upgrade-from and
a directory called upgrade-from.d. The first one will use the definition
of an upgrade for a specific role from upgrade-from.d. For now the SF repo
contains an example for an empty upgrade of the ldap role.

        ubuntu@sf-build:~/git/SoftwareFactory$ ls -al edeploy/upgrade-from.d/
        total 20
        drwxrwxr-x 2 ubuntu ubuntu 4096 Feb 27 17:58 .
        drwxrwxr-x 4 ubuntu ubuntu 4096 Feb 28 09:38 ..
        -rwxrwxr-x 1 ubuntu ubuntu   54 Feb 27 17:58 ldap_D7-H.1.0.0_D7-H.1.0.1.post
        -rwxrwxr-x 1 ubuntu ubuntu   53 Feb 27 17:58 ldap_D7-H.1.0.0_D7-H.1.0.1.pre
        -rwxrwxr-x 1 ubuntu ubuntu  106 Feb 27 17:58 ldap_D7-H.1.0.0_D7-H.1.0.1.upgrade

The .upgrade file contains the commands we want to perform to upgrade the target
file system (same as the .install file of a role).

To build the upgrade role of ldap for example :

       sudo ORIG=../../edeploy/build/ ./upgrade-from ldap D7-H.1.0.0 D7-H.1.0.1 /var/lib/debootstrap

The file system tree for the ldap role in version 1.0.1 is created in
/var/lib/debootstrap/install/D7-H.1.0.1 and metadata directory is created
in the current dir.

eDeploy server role provisionning
---------------------------------

Both install and metadata directories must be copied on the eDeploy server
deployed in the SF:

       sudo rsync -av /var/lib/debootstrap/install/D7-H.1.0.0/ldap -e "ssh -i /home/ubuntu/.ssh/id_rsa -l root" sf-edeploy-server:/var/lib/debootstrap/install/D7-H.1.0.0
       sudo rsync -av /var/lib/debootstrap/install/D7-H.1.0.1/ldap -e "ssh -i /home/ubuntu/.ssh/id_rsa -l root" sf-edeploy-server:/var/lib/debootstrap/install/D7-H.1.0.1
       sudo rsync -av metadata -e "ssh -i /home/ubuntu/.ssh/id_rsa -l root" sf-edeploy-server:/var/lib/debootstrap/

The /usr/sbin/edeploy command can be used from the sf-ldap node the verify that 1.0.1 version of the role
is available.

Migrate a project from Github
-----------------------------

The github plugin for Gerrit is a pain to build and
I never succeed to build and use it. The project
seems a bit new.

Migrate the source code of a project
....................................

This can be done with the manage tool of the SF using
the upstream key in the yaml configuration file.

Import pull requests of a project
.................................

The import-pr.py is a working POC based on this
Gist : https://gist.github.com/yuvipanda/5174162
that import all the commits of a pull request, squash
them and summit a review on Gerrit.

This tool does not handle the pull request'comments.
And I'm sure this can be improved.

Import the issues from Github to Redmine
........................................

It seems there is no existing tool for that over Internet.
It can be easy to write one using pyGithub and pyRedmine.

Next steps
----------

What need to be done in the next sprints:

* Use cloud-init to trigger puppet for the Gerrit role
* Add a main script based on Openstack API to deploy an
  configure all the roles: create images, register images
  in Glance if not done, start MySQL & LDAP instances, get IPs
  and update cloud-init settings for Jenkins, Gerrit and Redmine
* Store Git repositories on a Cinder volume for Gerrit and maybe for Redmine.
  The creation of the Cinder volume can be automated by the main script.
* Have a look to https://github.com/tru/redmine-gerrit-scripts
* Add Gitweb to the Gerrit eDeploy role.
* Have some specialized project parents pre-provisionned in Gerrit.
* Extend puppet manifests
* Secure instances, ie disable root logins / password logins
* Integrate puppet manifests into eNovance CI
* Jenkins role need git, nosetests, coverage, ...
* Jenkins job builder to automate job creation for gerrit new projects
* Jenkins new job should give link to failing test, and remove the 'nulljob/gerrit_tester/10' part
* Test VM updates using eDeploy
