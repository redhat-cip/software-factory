.. toctree::

Deploy Software Factory
=======================

Software Factory installation introduction
------------------------------------------

SF is designed to be installed on an OpenStack Cloud platform that embeds
Heat and Neutron. The installation is performed using Heat.
Basically you should just source your .openrc and setup a configuration file
before starting the start script.

However, to ease improving SF we have developed a way to deploy
the SF into LXC containers. Please have a look to the section `How to deploy SF within LXC`_

All the VM images needed by SF must be available locally or remotely.
The deployment process will take care of uploading those images to Glance.

OpenStack tenant requirements
.............................

The whole deployment of SF will use 7 VMs and 2 floating IPs. Be
sure to have enough resources before starting the Heat deployment.

Technical details regarding SF deployment on OpenStack
......................................................

The SF Heat deployment will spawn 7 virtual machines:
 - The puppet master node: This node embeds the puppet master
   service, the eDeploy server, and the SF bootstrapper controller.
 - The SQL database node: Gerrit, Redmine, Etherpad, Logdeit services
   use this VM as SQL backend.
 - The Gerrit node: Hosts only the Gerrit service.
 - The Redmine node: Hosts only the Redmine service.
 - The Jenkins master node: Hosts Jenkins master and ZUUL services
 - The Jenkins slave node: Where Jenkins master will trigger the tests.
 - The gateway node: Hosts the REST based service to manage projects and the
   central authentication service as well as the Etherpad, Lodgeit, Apache
   reverse proxy for all services, and the SSO server.

Security groups and needed floating IPs will be set by Heat.
Cloudinit will setup each VM but most of the configuration occurs
thanks to puppet. The puppet master node owns all the puppet manifests and
hiera configuration. The cloudinit script of the puppet master node
will first create all site specific keys and fill the hiera configuration
store, thanks to a little bootstrapper shell script. The bootstrapper
script will then trigger puppet agent on each node in order to configure all VMs.

Build or retrieve SF VM images
------------------------------

Software Factory role images can be created in two different formats.
Either the tree format (a directory that contains a full working filesystem) or
a bootable qcow2 image. The former is used to bootstrap a test environment
using LXC and the latter to deploy a production environment on an
OpenStack cloud. We use a tool called eDeploy to create role images.
All role images are based on CentOS 7.

To build or fetch the **latest stable version of Software Factory**
please set your local GIT copy of Software Factory to latest tag.
For instance, now the last tagged version is 0.9.2, so after having
cloned the repository :

.. code-block:: bash

 $ git tag -l # to list the available tags
 $ git checkout 0.9.2
 $ git checkout -b "0.9.2"

Indead, by using a tag, you will set the fetch_roles.sh script to use
pre-built images (trees or qcow2) that are freezed and known as stable.
Bootstrap scripts will use the tagged version too.

Use the master branch only if you want to help us to improve
Software Factory and if you like adventures :).

.. _fetchprebuilt:

Fetch pre-built SF images
.........................

Each patch merged on the Git SF master branch triggers a build of role
images of SF. That means if you clone the master branch of SF you will
be able to directly start the bootstrap script whether you want to
deploy a test platform on LXC or a production platform on an OpenStack
Cloud. Pre-built SF trees and images are available on a public
Swift container and the script called **fetch_roles.sh** will help
retrieve these. So first please clone the Software Factory
Git repository :

.. code-block:: bash

 $ git clone http://softwarefactory.enovance.com/r/software-factory

To fetch the pre-built SF trees in order to bootstrap a SF on LXC follow
the process below:

.. code-block:: bash

 $ ./fetch_roles.sh trees
 $ SF_SKIP_FETCHBASES=1 ./build_roles.sh
 $ ls -al /var/lib/sf/roles/install/C7.0-0.9.2/

A call of the script **build_roles.sh** is also needed in order to prepare the
local FS directory where the bootstrap scripts will look for the required trees
images.

To fetch the pre-built qcow2 images in order to bootstrap a SF on OpenStack
follow the process below:

.. code-block:: bash

 $ ./fetch_roles.sh imgs
 $ ls -al /var/lib/sf/roles/upstream/*.qcow2

You should find two qcow2 images: (install-server-vm, and softwarefactory).

Build SF images
...............

To build the images on your own (it is not advised to do so), follow the process
below. The build has been only tested on Ubuntu 14.04.1 LTS. So the
best is to install a VM with that Ubuntu version before trying
to build the SF images. Ensure that the current user can act as root
via sudo without password. If not you must login as root.

Some dependencies needs to be installed on your local system to build the images:

.. code-block:: bash

 $ sudo apt-get update
 $ sudo apt-get install build-essential debootstrap pigz python-dev python-pip unzip graphviz curl git kpartx
 $ sudo pip install Sphinx oslosphinx

You need to clone the Software Factory Git repository :

.. code-block:: bash

 $ git clone https://github.com/enovance/software-factory.git

Start the build of the VM images (this script will use sudo). If you want to
deploy on OpenStack you need to set the environment variable VIRT=true before
the build_roles.sh script.  The build may take a while :

.. code-block:: bash

 $ cd software-factory
 $ ./build_roles.sh
 $ ls -al /var/lib/sf/roles/install/C7.0-0.9.2/

The above command should have created two directories (install-server-vm, softwarefactory)
that contains the filesystem tree of the images you will need
to deploy the Software Factory. If you added **VIRT=true** qcow2 images have been created too. Those
will be used to deploy on OpenStack.

Note that the **build_roles.sh** script will try to fetch the pre-built images for
you from internet. Indeed, the default behavior of rebuilding is only useful if you have done
local changes on the SF edeploy roles. However if you really want to fully rebuild
please prefix the **build_roles.sh** script call with **SKIP_UPSTREAM=true**.

How to deploy SF on OpenStack
-----------------------------

Spawn your Software Factory
...........................

This step requires that VM images have been built: `Build or retrieve SF VM images`_.

Before spawning the SF on your tenant, be sure the quotas on your tenant will
allow to allocate :

 - 7 VMs
 - 2 Floating IPs
 - 4 Security groups
 - 1 Network

Register your public SSH key to your tenant. And retrieve the UUID of the external network by
using the following command :

.. code-block:: bash

 $ LC_ALL=C neutron net-list

Now you will need to adapt the sfconfig.yaml according to your needs "bootstrap/sfconfig.yaml".
Please read the explanations in the config file.

You will also need to configure some deployment details on top of the start.sh script
"bootstraps/heat/start.sh".

  - key_name : The name of public SSH key you just have registered
  - flavor : This is the default flavor to use. Be careful of your quotas.
  - alt_flavor : This flavor is used to host node that need more resources like Gerrit
    and Redmine.
  - ext_net_uuid : The UUID you have retrieved with the previous command.
  - sg_admin_cidr : The source network from where you can SSH to all SF nodes.
  - sg_user_cidr : The source network from where users can access SF services.

Assuming you have already built the SF role images, you will be able to deploy the SF. You just
need to source your OpenStack credentials into your shell environment:

.. code-block:: bash

 $ source openrc

.. code-block:: bash

 $ cd bootstraps/heat/
 $ FROMUPSTREAM=1 ./start.sh full_restart_stack

The start.sh script will take care of uploading role images to Glance and then
call heat stack-create. You have to wait a couple of minutes for the stack to
be created. Note the **FROMUPSTREAM** variable set to something to use upstream
images. If you want to use your modified images call **start.sh** without this
environment variable. You can check the progress using the following command:

.. code-block:: bash

 $ heat stack-list

Once stack-list reports stack-created status, you can use the option output-show to
display the floating IP of the puppetmaster node.

For now, once stack-created is reported it does not mean that the SF deployment
is completely done. Indeed stack-created reports that all resources defined
in the HEAT template are up but a couple of scripts and puppet agents need
to finish their work before you can use your SF deployment.

So once the stack is created you can connect using SSH on
the puppetmaster node using the root user (your SSH public key has been added to
the root's authorized_keys file) and wait for the file
/root/puppet-bootstrapper/build/bootstrap.done to be created.

.. code-block:: bash

 $ heat output-show SoftwareFactory puppetmaster_public_address
 $ ssh root@puppetmaster_public_address ls /root/puppet-bootstrapper/build/bootstrap.done

This file is created once all scripts and puppet agents have finished to apply the
manifests to configure all SF services.

On the puppetmaster node the file /var/log/sf-bootstrap.log contains the
log of the bootstrap process. You can follow the process using :

.. code-block:: bash

 $ ssh root@puppetmaster_public_address tailf /var/log/sf-bootstrap.log

The Software Factory HTTP gateway is accessible on the managesf
IP address via HTTP. You can retrieve the managesf floating IP using :

.. code-block:: bash

 $ heat output-show SoftwareFactory managesf_public_address

You need to use the domain you have configured in sfconfig.yaml (by default: tests.dom)
to access the Software Factory HTTP gateway. So be sure that your DNS resolves the domain to
the right IP or configure your /etc/hosts locally.

Troubleshooting deployment problems
...................................

In case of a heat deployment the stack creation can fail due to resource
allocation problems on the OpenStack cloud, for instance if resources are
restricted by quotas.

To look at the error messages you can perform the following command:

.. code-block:: bash

 $ heat stack-show SoftwareFactory

Failures can also occur during puppet agents runs. You can have a look to all
puppet logs on the puppetmaster node in /var/log/sf-bootstrap.log.

.. _lxcdeploy:

How to deploy SF within LXC
---------------------------

The LXC deployment is a deployment method that should only be used
for test deployments. Only the SF deployment method for OpenStack is targeted
for production.

This step requires that VM images have been built `Build or retrieve SF VM images`_.

The LXC deployment has been only tested on Ubuntu 14.04 LTS. We advice to
setup an Ubuntu 14.04 VM somewhere either on OpenStack or VirtualBox or wherever
you prefer. Please make sure your instance is up-to-date:

.. code-block:: bash

 $ sudo apt-get update
 $ sudo apt-get upgrade

If there were any kernel updates applied you also need to reboot.

Now install the following dependencies:

.. code-block:: bash

 $ sudo apt-get install linux-image-extra-$(uname -r) git python-augeas bridge-utils curl lxc libmysqlclient-dev \
 libssl-dev swig libldap2-dev libsasl2-dev python-dev python-pip graphviz
 $ sudo pip install flake8 bash8
 $ sudo pip install -U tox==1.6.1 virtualenv==1.10.1 Sphinx oslosphinx

The commands above also installs the requirements to run the unit tests of some
of the tools included in SF.

Edeploy-lxc must be installed to ease container provision based on
images created by Edeploy. So please execute the following command:

.. code-block:: bash

 $ sudo git clone https://github.com/enovance/edeploy-lxc.git /srv/edeploy-lxc

The default SF configuration file bootstrap/sfconfig.yaml is ready to use
for the LXC deployment. However you can still configure it if the defaults
are not convenient for you.

Ensure that the current user can act as root via sudo without password.
If not you must login as root. The current user must have a RSA public
key available in $HOME/.ssh, if not please create it before with ssh-keygen
without a passphrase.

In order to start the SF deployment perform the commands below:

.. code-block:: bash

 $ cd bootstraps/lxc
 $ ./start.sh
 $ sudo lxc-ls -f

The lxc-ls command should report the following :

.. code-block:: none

 NAME          STATE    IPV4            IPV6  AUTOSTART
 ------------------------------------------------------
 gerrit        RUNNING  192.168.134.52  -     NO
 jenkins       RUNNING  192.168.134.53  -     NO
 managesf      RUNNING  192.168.134.54  -     NO
 mysql         RUNNING  192.168.134.50  -     NO
 puppetmaster  RUNNING  192.168.134.49  -     NO
 redmine       RUNNING  192.168.134.51  -     NO
 slave         RUNNING  192.168.134.55  -     NO

You can follow the bootstrap process by connecting to the
puppetmaster node and tail -f /var/log/sf-bootstrap.log:

.. code-block:: bash

 $ ssh root@192.168.134.49 tail -f /var/log/sf-bootstrap.log

Once the bootstrap is done your demo SF deployment is ready to be used.
Assuming you have not modified the default domain in sfconfig.yaml "tests.dom",
add an entry to your workstation's /etc/hosts to resolve tests.dom
to "the public IP of the VM where LXC containers are running" and setup a TCP
tunnel from localhost:80 to 192.168.134.54:80 using the socat tool on the VM.

.. code-block:: bash

 $ sudo socat TCP-LISTEN:www,fork TCP4:192.168.134.54:www

Then open your browser on http://tests.dom (TCP/80 must be allowed
from your workstation to the VM). Assuming the used domain is tests.dom,
you can use the default pre-provisioned users that are user1, user2,
user3 with 'userpass' as password. User *user1* is the default administrator
in this LXC SF deployment.

NOTE: Be careful that running again the start.sh command will
wipe the previous deployment.

You can stop all the SF LXC containers using:

.. code-block:: bash

 $ cd bootstraps/lxc
 $ ./start.sh stop

Troubleshooting lxc deployment
..............................

The containers have no access to external resources. If you need to open outbound
traffic on the containers, run the following command on the host:

.. code-block:: bash

 $ sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

where *eth0* is your main network interface.

The default admin user
----------------------

You need a default admin user to create new repositories, modify ACLs and
assign users to projects.  By default this is *user1*, defined in
"bootstrap/sfconfig.yaml". You can change this user before deploying SF, and
even use an existing Github username.  If an user logins using the login form (with
username and password) it will be authenticated locally, even if there is no
LDAP backend defined.
The password of this user is hashed and salted and stored on the managesf node.
By default this is *userpass*.  Use the following command to compute a new
password:

.. code-block:: bash

 $ mkpasswd -m sha-512 "secret_password"

The password is also stored in plaintext in bootstrap/sfconfig.yaml, because it
is needed by Puppet to create default accounts. You can set the plaintext
password to "" after the initial deployment is done (both in
bootstrap/sfconfig.yaml and in  /etc/puppet/hiera/sf/sfconfig.yaml).

Github authentication
---------------------

You have to register your SF deployment in Github to enable Github
authentication.

#. Login to your Github account, go to Settings -> Applications -> "Register new application"
#. Fill in the details and be careful when setting the authorization URL. It will look like this: http://yourdomain/auth/login/github/callback
#. Set the corresponding values in bootstrap/sfconfig.yaml:
    - github_app_id: "Client ID"
    - github_app_secret: "Client Secret"
    - github_allowed_organization: comma-separated list of organizations that are allowed to access this SF deployment. A user has to be member of at least one of this organizations to use this SF deployment. Leave empty if not required.
