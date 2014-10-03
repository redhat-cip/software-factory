.. toctree::

Deploy Software Factory
=======================

Sofware Factory installation introduction
-----------------------------------------

SF is designed to be installed on an Openstack Cloud platform that embed
Heat and Neutron. The installation is performed using Heat.
Basically you should just source your .openrc and setup a configuration file
before starting the start script.

Howerver, to ease improving SF we have developed a way to deploy
the SF into LXC containers. Please have a look to the section `How to deploy SF within LXC`_

All the VM images need by SF must be available locally or remotely.
The deployment process will take care of uploading those images in Glance.

Openstack tenant requirements
.............................

The whole deployment of SF will uses 7 VMs and 2 floating IPs. Be
sure to have enough resourses before starting the Heat deployment.

Technical details regarding SF deployment on OpenStack
......................................................

The SF Heat deployment will spawn 7 virtual machines:
 - The puppet master node : This node embeds the puppet master
   service, the eDeploy server, and the SF bootstraper controler.
 - The SQL database node : Gerrit, Redmine, Etherpad, Logdeit services
   use this VM as SQL backend.
 - The Gerrit node: Hosts only the Gerrit service.
 - The Redmine node: Hosts only the Redmine service.
 - The Jenkins master node: Hosts Jenkins master and ZUUL services
 - The Jenkins slave node: Where Jenkins master will triggers the tests.
 - The gateway node: Host the REST based service to manage projects and the
   central authentication service as well as the Etherpad, Lodgeit, Apache
   reverse proxy for all services, and the SSO server.

Security groups and nedeed floating IPs will be set by Heat.
Cloudinit will setup each VM but most of the configuration occurs
thanks to puppet. The puppet master node owns all the puppet manifests and
hiera configuration. The cloudinit script of the puppet master node
will first create all site specific keys and fill the hiera configuration
store, thanks to a little boostrapper shell script. The bootstrapper
script will then trigger puppet agent on each node in order to configure all VMs.

Build or retrieve SF VM images
------------------------------

Pre-built VM images are not available yet.

Images are based on CentOS 7.

To build the images by your own (it is not adviced to do so), follow the process
below. The build has been only tested on Ubuntu 14.04.1 LTS. So the
best is to install a VM with that Ubuntu version before trying
to build the SF images. Ensure that the current user can act as root
via sudo without password. If not you must login as root.

You need to clone the Software Factory Git repository :

.. code-block:: bash

 $ git clone https://github.com/enovance/SoftwareFactory.git

Some dependencies needs to be installed on your local system to build the images:

.. code-block:: bash

 $ sudo apt-get install build-essential debootstrap pigz python-dev python-pip unzip graphviz curl git
 $ sudo pip install Sphinx oslosphinx

Start the build of the VM images (this script will use sudo). If you want to
deploy on Openstack you need to add before the build_roles.sh script
the environment variable VIRT=true. The build may take a while :

.. code-block:: bash

 $ SF_DIST=CentOS ./build_roles.sh
 $ ls -al /var/lib/sf/roles/install/C7.0-0.9.2/

The above command should have produced four directories (install-server-vm, mysql, slave, softwarefactory)
that contains the filesystem tree of the images you will need
to deploy the Software Factory. If you added VIRT=true qcow2 images have been created too. Those
will be used to deploy on OpenStack.

How to deploy SF on OpenStack
-----------------------------

Spawn your Software Factory
...........................

This step require that VM images has been built `Build or retrieve SF VM images`_.

Before spawning the SF on your tenant, be sure the quotas on your tenant will
allow to allocate :

 - 7 VMs
 - 2 Floating IPs
 - 5 Security groups
 - 1 Network

Register your public SSH key to your tenant. And retrieve the UUID of the external network by
using the following command :

.. code-block:: bash

 $ LC_ALL=C neutron net-list

Now you will need to adapt the sfconfig.yaml according to your needs "bootstrap/sfconfig.yaml".
Please read the explantions in the config file.

You will also need to configure some deployment details on top of the start.sh script
"bootstrap/heat/start.sh".

  - key_name : The name of public SSH key you just have registered
  - flavor : This is the defaut flavor to use. Be careful of your quotas.
  - alt_flavor : This flavor is used to host node that need more resourses like Gerrit
    and Redmine.
  - ext_net_uuid : The UUID you have retrieved by the previous command.
  - sg_admin_cidr : The source network from where you can SSH to all SF nodes.
  - sg_user_cidr : The source network from where users can access SF services.

Assuming you have already built the SF role images, you will be able to deploy the SF. You just
need to source in your shell environment yours OpenStack credentials:

.. code-block:: bash

 $ source openrc

.. code-block:: bash

 $ cd bootstraps/heat/
 $ ./start.sh full_restart_stack

The start.sh script will take care of uploading role images to Glance and then
call heat stack-create. You have to wait a couple of minutes for the stack to
created. You can check the progress using the following command.

.. code-block:: bash

 $ heat stack-show SoftwareFactory

Once stack-show reports stack-created status, you can use output-show option to
display the puppetmaster node floating IP.

For now, once stack-created is reported does not mean that the SF deployment
is completly done. Indeed stack-created reports that all resourse defined
in the HEAT template are up but a couple of script and puppet agents need
to finish their work before you can use your SF deployment.

So once the stack is create you can connect using SSH on
the puppetmaster node using the root user (your SSH public key has been added to
the root's authorized_keys file) and wait for the file
/root/puppet-bootstrapper/build/bootstrap.done to be create.

This file is created once all scripts and puppet agents has finished to play their
manifests to configure all SF services.

On the pupetmaster node the file /var/log/sf-bootstrap.log contained the
log of the bootstrap process.

The Software Factory HTTP gateway is accessible on the managesf
IP address via HTTP. You can retrieve the managesf floating IP via :

.. code-block:: bash

 $ heat output-show

Troubleshooting deployment problems
...................................

In case of a heat deployment the stack creation can fail due to resources
allocations problems on the OpenStack cloud you use for instance if resources
allocation are restricted by quotas.

To look at the error messages you can perform the following command:

.. code-block:: bash

 $ heat stack-show SoftwareFactory

Failures can aslo occur during puppet agents runs. You can have a look to all
puppet logs on the puppetmaster node in /var/log/sf-bootstrap.log.

How to deploy SF within LXC
---------------------------

The LXC deployment is a deployment method that should only be used
for test deployments. Only the SF deployment method for OpenStack is targeted
for production.

This step require that VM images has been built `Build or retrieve SF VM images`_.

The LXC deployment has been only tested on Ubuntu 14.04 LTS. We advice to
setup an Ubuntu 14.04 VM somewhere either on Openstack or VirtualBox or where
you prefer. Following the dependencies installation instructions below:

.. code-block:: bash

 $ sudo apt-get install install linux-image-extra-$(uname -r) git python-augeas bridge-utils curl lxc libmysqlclient-dev \
 libssl-dev swig libldap2-dev libsasl2-dev python-dev graphviz
 $ sudo pip install flake8 bash8
 $ sudo pip install -U tox==1.6.1 virtualenv==1.10.1 Sphinx oslosphinx

The commands above also install the requirements to run the unit tests of some
of the tools included in SF.

Edeploy-lxc must be installed to ease container provision based on
images created by Edeploy. So please execute the following command:

.. code-block:: bash

 $ sudo git clone https://github.com/enovance/edeploy-lxc.git /srv/edeploy-lxc

The default SF configuration file bootstrap/sfconfig.yaml is ready to use
for the LXC deployement. However if you can still configure it if default
is not convenient for you.

Ensure that the current user can act as root via sudo without password.
If not you must login as root. In order to start the SF deployment perform
the commands below:

.. code-block:: bash

 $ cd bootstrap/lxc
 $ ./start.sh
 $ sudo lxc-ls -f

The lxc-ls command should report the folowing :

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

 $ ssh root@192.168.134.49 tailf /var/log/sf-bootstrap.log

Once the bootstrap in done. Your demo SF deployment is ready to be used.
Assuming you have let the default domain in sfconfig.yaml "tests.dom" configure
your /etc/hosts to resolve tests.dom to 192.156.134.54.

Then open your browser on http://tests.dom. Always assuming the used
domain is tests.dom, you can use the default pre-provisioned users
that are user1, user2, user3 with 'userpass' as password. User
user1 is the default administrator the SF deployment.

NOTE: Be careful that runinng again the start.sh command will
wipe the previous deployment.
