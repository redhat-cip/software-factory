Contents:

.. toctree::

Administrate the Software Factory
=================================

Sofware Factory installation introduction
-----------------------------------------

SF is designed to be installed on an Openstack Cloud platform that embed
Heat and Neutron. The installation is performed using Heat.
Basically you should just source your .openrc before starting the start
script.

All the VM images need by SF must be available locally or remotely.
The deployment process will take care of uploading those images in Glance.

Openstack tenant requirements
.............................

The whole deployment of SF will uses 9 VMs and 3 floating IPs. Be
sure to have enough resourses before starting the Heat deployment.

Technical details regarding SF deployment
.........................................

The SF Heat deployment will spawn 9 virtual machines:
 - The puppet master node : This node embeds the puppet master
   service, the eDeploy server, and the bootstraper controler.
 - The Mysql node : Gerrit, Redmine, Etherpad, Logdeit services
   use this VM as SQL backend.
 - The Ldap node: This node is used for user authentication.
 - The Gerrit node: Hosts only the Gerrit service.
 - The Redmine node: Hosts only the Redmine service.
 - The Jenkins master node: Hosts Jenkins master and ZUUL services
 - The Jenkins slave node: Where Jenkins master will triggers the tests.
 - The commonservices node: Hosts Etherpad, Lodgeit, the Apache reverse proxy
   for all services, and the SSO server.
 - The managesf node: Host the REST based service to manage projects and the 
   central authentication service

Security groups and nedeed floating IPs will be set by Heat.
Cloudinit will setup each VM but most of the configuration occurs
thanks to puppet. The puppet master node owns all the puppet manifests and
hiera configuration. The cloudinit script of the puppet master node
will first create all site specific keys and fill the hiera configuration
store, thanks to a little boostrapper shell script. The bootstrapper
script will trigger puppet agent on each node in order to configure all VMs.

How to deploy the SF
--------------------

Create or retrieve VM images
............................

VM images are available here <to complete>. You shoud copy it locally
before triggering the heat bootstrapping. <to complete>.

To build the images by your own (it is not adviced to do so), follow this process
below. The build has been only tested on Ubuntu 12.04 LTS. So the
best is to install a VM with that Ubuntu version before trying
to build the SF images. Ensure that the current user can act as root
via sudo without password. If not you must login as root.

You need to clone the Software Factory Git repository :

.. code-block:: bash

    $ git clone https://github.com/enovance/SoftwareFactory.git

Some dependencies needs to be installed on your local system :

.. code-block:: bash

    # apt-get install build-essential debootstrap pigz python-dev python-pip unzip

Start the build of the VM images (this script will use sudo). This may
take a while :

.. code-block:: bash

    $ VIRT=true ./build_roles.sh
    $ ls -al /var/lib/sf/roles/D7-H.0.9.0/*.img*

The above command should have produced all the qcow2 images you will need
to deploy the Software Factory.

Spawn your Software Factory
...........................

Before spawning the SF on your tenant, be sure the quotas on your tenant will
allow to allocate :
 
 - 9 VMs
 - 3 Floating IPs
 - 5 Security groups
 - 1 Network

Register your public SSH key to your tenant. Retrieve the UUID of the external network by
using the following command :

.. code-block:: bash

    $ LC_ALL=C neutron net-list

Now you will need to change some informations on the top of the bootstraps/heat/start.sh
file :
  
  - key_name : The name of public SSH key you just have registered
  - flavor : This is the defaut flavor to use. Be careful of your quotas.
  - alt_flavor : This flavor is used to host node that need more resourses like Gerrit
    and Redmine.
  - suffix : It is the domain of your futur SF platform. It will be used by the SSO feature.
  - ext_net_uuid : The UUID you have retrieved by the previous command.
  - sg_admin_cidr : The source network from where you can SSH to all SF nodes.
  - sg_user_cidr : The source network from where users can access SF services.

Assuming you have already built the SF role images, you will be able to deploy the SF, but
you need to source in your shell environment yours credentials :

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
display the puppetmaster node floating IP. Please connect using SSH on
that node using the root user (your SSH public key has been added to
the root's authorized_keys file). Wait for the file
/root/puppet-bootstrapper/build/bootstrap.done to be there. This file is
created once all puppet agents has finished to play their manifests to
configure all SF services.

The Software Factory Apache gateway is accessible on the commonservices
IP address via HTTP. You can retrieve the commonservices floating
IP via heat output-show.

Troubleshooting deployment problems
...................................

The heat stack creation can fail due to resources allocations problems you use
heat stack-show SoftwareFactory to looked at the error message.

Failures can occur during puppet agents runs. You can have a look to all
puppet logs on the puppetmaster node in /var/log/sf-bootstrap.log.
